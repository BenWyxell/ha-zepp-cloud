from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo
import json


_SYSTOLIC_KEYS = (
    "systolic",
    "systolicPressure",
    "highPressure",
    "high",
    "sbp",
    "upper",
)
_DIASTOLIC_KEYS = (
    "diastolic",
    "diastolicPressure",
    "lowPressure",
    "low",
    "dbp",
    "lower",
)
_PULSE_KEYS = ("pulse", "heartRate", "heart_rate", "hr")
_TIME_KEYS = (
    "timestamp",
    "time",
    "measureTime",
    "measurementTime",
    "dateTime",
    "measuredAt",
    "createTime",
    "createdAt",
)
_SOURCE_KEYS = ("source", "sourceName", "deviceSource", "appSource")


def parse_blood_pressure(payload: Any, tz_name: str) -> dict[str, Any]:
    """Parse blood-pressure history returned by Zepp.

    The Zepp endpoint is private and response keys vary between app/device
    generations. This parser deliberately accepts several observed/common key
    aliases while requiring a plausible systolic + diastolic pair before a
    record is treated as a measurement.
    """
    out: dict[str, Any] = {
        "blood_pressure": None,
        "blood_pressure_systolic": None,
        "blood_pressure_diastolic": None,
        "blood_pressure_pulse": None,
        "blood_pressure_time": None,
        "blood_pressure_source": None,
        "blood_pressure_measurements_today": 0,
        "blood_pressure_systolic_min_today": None,
        "blood_pressure_systolic_max_today": None,
        "blood_pressure_systolic_avg_today": None,
        "blood_pressure_diastolic_min_today": None,
        "blood_pressure_diastolic_max_today": None,
        "blood_pressure_diastolic_avg_today": None,
    }

    records: list[dict[str, Any]] = []
    _walk(payload, records, {})
    if not records:
        return out

    measurements: list[dict[str, Any]] = []
    for record in records:
        systolic = _first_number(record, _SYSTOLIC_KEYS)
        diastolic = _first_number(record, _DIASTOLIC_KEYS)
        if systolic is None or diastolic is None:
            continue

        # Conservative sanity bounds prevent unrelated high/low fields from
        # accidentally becoming a blood-pressure reading.
        if not (50 <= systolic <= 280 and 30 <= diastolic <= 200):
            continue
        if systolic <= diastolic:
            continue

        measured_at = _first_time(record, _TIME_KEYS)
        pulse = _first_number(record, _PULSE_KEYS)
        if pulse is not None and not 25 <= pulse <= 250:
            pulse = None

        source = None
        for key in _SOURCE_KEYS:
            value = record.get(key)
            if isinstance(value, (str, int, float)) and str(value).strip():
                source = str(value)
                break

        measurements.append(
            {
                "systolic": systolic,
                "diastolic": diastolic,
                "pulse": pulse,
                "time": measured_at,
                "source": source,
            }
        )

    if not measurements:
        return out

    # Prefer timestamp ordering. Untimestamped records remain usable but sort
    # behind timestamped measurements.
    measurements.sort(
        key=lambda item: item["time"].timestamp() if item["time"] else -1
    )
    latest = measurements[-1]

    systolic = latest["systolic"]
    diastolic = latest["diastolic"]
    out.update(
        {
            "blood_pressure": f"{_display_number(systolic)}/{_display_number(diastolic)}",
            "blood_pressure_systolic": systolic,
            "blood_pressure_diastolic": diastolic,
            "blood_pressure_pulse": latest["pulse"],
            "blood_pressure_time": latest["time"],
            "blood_pressure_source": latest["source"],
        }
    )

    try:
        tz = ZoneInfo(tz_name)
    except (KeyError, ValueError):
        tz = timezone.utc
    today = datetime.now(tz).date()

    today_values = [
        item
        for item in measurements
        if item["time"] is not None and item["time"].astimezone(tz).date() == today
    ]
    out["blood_pressure_measurements_today"] = len(today_values)

    if today_values:
        sys_values = [float(item["systolic"]) for item in today_values]
        dia_values = [float(item["diastolic"]) for item in today_values]
        out.update(
            {
                "blood_pressure_systolic_min_today": _nice(min(sys_values)),
                "blood_pressure_systolic_max_today": _nice(max(sys_values)),
                "blood_pressure_systolic_avg_today": round(
                    sum(sys_values) / len(sys_values), 1
                ),
                "blood_pressure_diastolic_min_today": _nice(min(dia_values)),
                "blood_pressure_diastolic_max_today": _nice(max(dia_values)),
                "blood_pressure_diastolic_avg_today": round(
                    sum(dia_values) / len(dia_values), 1
                ),
            }
        )

    return out


def _walk(
    value: Any,
    records: list[dict[str, Any]],
    inherited: dict[str, Any],
) -> None:
    """Collect dictionaries while carrying parent timestamp/source metadata."""
    if isinstance(value, dict):
        context = dict(inherited)
        for key in (*_TIME_KEYS, *_SOURCE_KEYS):
            if key in value:
                context[key] = value[key]

        merged = {**context, **value}
        records.append(merged)
        for child in value.values():
            _walk(child, records, context)
        return

    if isinstance(value, list):
        for child in value:
            _walk(child, records, inherited)
        return

    if isinstance(value, str):
        text = value.strip()
        if not text or text[0] not in "[{":
            return
        try:
            decoded = json.loads(text)
        except (ValueError, TypeError):
            return
        _walk(decoded, records, inherited)


def _first_number(record: dict[str, Any], keys: tuple[str, ...]) -> float | int | None:
    for key in keys:
        if key not in record:
            continue
        value = _number(record.get(key))
        if value is not None:
            return value
    return None


def _number(value: Any) -> float | int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            number = float(value.strip())
        except ValueError:
            return None
        return int(number) if number.is_integer() else number
    return None


def _first_time(record: dict[str, Any], keys: tuple[str, ...]) -> datetime | None:
    for key in keys:
        if key not in record:
            continue
        parsed = _parse_time(record.get(key))
        if parsed is not None:
            return parsed
    return None


def _parse_time(value: Any) -> datetime | None:
    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        number = float(value)
        if number > 10_000_000_000:
            number /= 1000.0
        try:
            return datetime.fromtimestamp(number, tz=timezone.utc)
        except (ValueError, OSError, OverflowError):
            return None

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            number = float(text)
        except ValueError:
            number = None
        if number is not None:
            return _parse_time(number)
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    return None


def _nice(value: float) -> float | int:
    return int(value) if float(value).is_integer() else value


def _display_number(value: float | int) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:g}"
