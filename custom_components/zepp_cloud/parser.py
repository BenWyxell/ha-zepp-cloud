from __future__ import annotations

import base64
import json
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo


def _safe_json(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str) or not value:
        return None
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return None


def _items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return [x for x in payload["items"] if isinstance(x, dict)]
    return []


def _decode_b64(value: str | None) -> bytes:
    if not value:
        return b""
    try:
        return base64.b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, TypeError):
        return b""


def decode_summary(encoded: str | None) -> dict[str, Any]:
    raw = _decode_b64(encoded)
    if not raw:
        return {}
    try:
        decoded = json.loads(raw.decode("utf-8"))
        return decoded if isinstance(decoded, dict) else {}
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}


def decode_heart_rate_day(
    row: dict[str, Any],
    tz_name: str,
) -> list[tuple[datetime, int]]:
    """Decode one day of minute heart-rate data.

    Preferred source:
      `data_hr`: 1440 bytes, one minute value per byte.

    Fallback:
      `data`: N x byteLength minute records. For the known Zepp 8-byte record
      layout, byte index 3 matches the heart-rate series.

    Missing/sentinel values 0/254/255 and implausible values are ignored.
    """
    day_value = row.get("date_time")
    if not isinstance(day_value, str):
        return []

    summary = decode_summary(row.get("summary"))
    byte_length = int(_number(summary.get("byteLength")) or 8)

    direct = _decode_b64(row.get("data_hr"))
    fallback = _decode_b64(row.get("data"))

    values: list[int] = []
    if len(direct) >= 1440:
        values = [int(v) for v in direct[:1440]]
    elif byte_length >= 4 and len(fallback) >= byte_length:
        count = min(1440, len(fallback) // byte_length)
        values = [
            int(fallback[i * byte_length + 3])
            for i in range(count)
        ]

    if not values:
        return []

    try:
        d = date.fromisoformat(day_value)
        tz = ZoneInfo(tz_name)
    except (ValueError, KeyError):
        return []

    start = datetime.combine(d, time.min, tzinfo=tz)
    result: list[tuple[datetime, int]] = []
    for minute, hr in enumerate(values):
        if 30 <= hr <= 240:
            result.append((start + timedelta(minutes=minute), hr))
    return result


def parse_band_data(payload: Any, tz_name: str) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        rows = [x for x in payload["data"] if isinstance(x, dict)]

    out: dict[str, Any] = {
        "heart_rate": None,
        "heart_rate_time": None,
        "heart_rate_min_today": None,
        "heart_rate_max_today": None,
        "heart_rate_avg_today": None,
        "heart_rate_samples_today": 0,
        "steps": None,
        "distance_km": None,
        "sleep_score": None,
        "sleep_total_min": None,
        "sleep_light_min": None,
        "sleep_deep_min": None,
        "sleep_rem_min": None,
        "sleep_awake_min": None,
        "sleep_resting_hr": None,
        "sleep_start": None,
        "sleep_end": None,
        "sleep_awakenings": None,
        "sleep_stage_segments": [],
        "sleep_date": None,
        "_heart_rate_series": [],
    }
    if not rows:
        return out

    rows.sort(key=lambda x: str(x.get("date_time") or ""))

    latest = rows[-1]
    summary = decode_summary(latest.get("summary"))
    step = summary.get("stp") if isinstance(summary.get("stp"), dict) else {}
    out["steps"] = _number(step.get("ttl"))
    distance_m = _number(step.get("dis"))
    if distance_m is not None:
        out["distance_km"] = round(float(distance_m) / 1000.0, 3)

    hr_series = decode_heart_rate_day(latest, tz_name)
    out["_heart_rate_series"] = [
        {"time": dt.isoformat(), "value": hr} for dt, hr in hr_series
    ]
    if hr_series:
        now = datetime.now(ZoneInfo(tz_name))
        usable = [(dt, hr) for dt, hr in hr_series if dt <= now + timedelta(minutes=2)]
        if usable:
            dt, hr = usable[-1]
            values = [v for _, v in usable]
            out["heart_rate"] = hr
            out["heart_rate_time"] = dt
            out["heart_rate_min_today"] = min(values)
            out["heart_rate_max_today"] = max(values)
            out["heart_rate_avg_today"] = round(sum(values) / len(values), 1)
            out["heart_rate_samples_today"] = len(values)

    for row in reversed(rows):
        sm = decode_summary(row.get("summary"))
        slp = sm.get("slp") if isinstance(sm.get("slp"), dict) else {}
        if not slp or not slp.get("st") or not slp.get("ed"):
            continue

        stages = slp.get("stage") if isinstance(slp.get("stage"), list) else []
        mode_minutes: dict[int, int] = {}
        clean_stages: list[dict[str, int]] = []
        for segment in stages:
            if not isinstance(segment, dict):
                continue
            try:
                mode = int(segment.get("mode"))
                start = int(segment.get("start"))
                stop = int(segment.get("stop"))
            except (TypeError, ValueError):
                continue
            minutes = max(0, stop - start + 1)
            mode_minutes[mode] = mode_minutes.get(mode, 0) + minutes
            clean_stages.append({"start": start, "stop": stop, "mode": mode})

        light = _number(slp.get("lt"))
        deep = _number(slp.get("dt"))
        rem = mode_minutes.get(5, 0)
        awake = mode_minutes.get(7, 0)

        total = None
        if light is not None or deep is not None or rem:
            total = int(light or 0) + int(deep or 0) + int(rem or 0)

        out.update(
            {
                "sleep_score": _number(slp.get("ss")),
                "sleep_total_min": total,
                "sleep_light_min": light,
                "sleep_deep_min": deep,
                "sleep_rem_min": rem,
                "sleep_awake_min": awake,
                "sleep_resting_hr": _number(slp.get("rhr")),
                "sleep_start": _timestamp_seconds(slp.get("st")),
                "sleep_end": _timestamp_seconds(slp.get("ed")),
                "sleep_awakenings": _number(slp.get("wc")),
                "sleep_stage_segments": clean_stages,
                "sleep_date": row.get("date_time"),
            }
        )
        break

    return out


def parse_daily_health(payload: Any) -> dict[str, Any]:
    result = {
        "steps": None,
        "calories": None,
        "active_minutes": None,
        "step_goal": None,
        "calorie_goal": None,
        "active_minutes_goal": None,
        "step_goal_progress": None,
        "calorie_goal_progress": None,
        "active_minutes_goal_progress": None,
    }
    candidates: list[dict[str, Any]] = []
    for item in _items(payload):
        value = item.get("value")
        if not isinstance(value, dict):
            continue
        samples = value.get("samples")
        if isinstance(samples, list):
            candidates.extend(x for x in samples if isinstance(x, dict))
    if not candidates:
        return result

    candidates.sort(key=lambda x: str(x.get("dateString") or ""))
    s = candidates[-1]

    result.update(
        {
            "steps": _number(s.get("totalSteps")),
            "calories": _number(s.get("totalCalories")),
            "active_minutes": _number(s.get("totalBurningDuration")),
            "step_goal": _number(s.get("stepGoal")),
            "calorie_goal": _number(s.get("calorieGoal")),
            "active_minutes_goal": _number(s.get("burningDurationGoal")),
        }
    )
    result["step_goal_progress"] = _percent(result["steps"], result["step_goal"])
    result["calorie_goal_progress"] = _percent(result["calories"], result["calorie_goal"])
    result["active_minutes_goal_progress"] = _percent(
        result["active_minutes"], result["active_minutes_goal"]
    )
    return result


def parse_stress(payload: Any) -> dict[str, Any]:
    out = {
        "stress": None,
        "stress_time": None,
        "stress_avg": None,
        "stress_min": None,
        "stress_max": None,
    }
    points: list[tuple[int, float]] = []
    newest_item: dict[str, Any] | None = None

    for item in _items(payload):
        if newest_item is None or int(item.get("timestamp") or 0) > int(
            newest_item.get("timestamp") or 0
        ):
            newest_item = item
        data = _safe_json(item.get("data"))
        if isinstance(data, list):
            for point in data:
                if not isinstance(point, dict):
                    continue
                ts = _number(point.get("time"))
                val = _number(point.get("value"))
                if ts is not None and val is not None:
                    points.append((int(ts), float(val)))

    if points:
        points.sort(key=lambda x: x[0])
        ts, value = points[-1]
        out["stress"] = int(value) if value.is_integer() else value
        out["stress_time"] = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)

    if newest_item:
        out["stress_avg"] = _number(newest_item.get("avgStress"))
        out["stress_min"] = _number(newest_item.get("minStress"))
        out["stress_max"] = _number(newest_item.get("maxStress"))
    return out


def parse_spo2(payload: Any) -> dict[str, Any]:
    points: list[tuple[int, float]] = []

    def walk(obj: Any, inherited_ts: int | None = None) -> None:
        if isinstance(obj, str):
            parsed = _safe_json(obj)
            if parsed is not None:
                walk(parsed, inherited_ts)
            return
        if isinstance(obj, list):
            for x in obj:
                walk(x, inherited_ts)
            return
        if not isinstance(obj, dict):
            return

        ts = inherited_ts
        for key in ("time", "timestamp", "dateTime", "measureTime"):
            val = _number(obj.get(key))
            if val is not None:
                ts = int(val)
                if ts < 10_000_000_000:
                    ts *= 1000
                break

        for key, value in obj.items():
            normalized = key.lower().replace("_", "")
            if normalized in {
                "spo2",
                "bloodoxygen",
                "bloodoxygenvalue",
                "oxygen",
                "oxygenvalue",
            }:
                val = _number(value)
                if val is not None and 50 <= float(val) <= 100:
                    points.append((ts or 0, float(val)))

        for value in obj.values():
            if isinstance(value, (dict, list, str)):
                walk(value, ts)

    walk(payload)
    if not points:
        return {"spo2": None, "spo2_time": None}

    points.sort(key=lambda x: x[0])
    ts, value = points[-1]
    return {
        "spo2": int(value) if value.is_integer() else value,
        "spo2_time": (
            datetime.fromtimestamp(ts / 1000, tz=timezone.utc) if ts else None
        ),
    }


def parse_training_load(payload: Any) -> dict[str, Any]:
    items = _items(payload)
    if not items:
        return {"training_load": None, "day_training_load": None}
    items.sort(key=lambda x: str(x.get("dayId") or ""))
    latest = items[-1]
    return {
        "training_load": _number(latest.get("wtlSum")),
        "day_training_load": _number(latest.get("currnetDayTrainLoad")),
    }


def parse_vo2(payload: Any) -> dict[str, Any]:
    items = _items(payload)
    if not items:
        return {"vo2_max": None}
    items.sort(key=lambda x: str(x.get("dayId") or x.get("timestamp") or ""))
    latest = items[-1]

    for key in ("vo2Max", "vo2max", "value", "v", "watchValue"):
        val = _number(latest.get(key))
        if val is not None and 10 <= float(val) <= 100:
            return {"vo2_max": val}

    def find(obj: Any) -> float | int | None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                if "vo2" in key.lower():
                    val = _number(value)
                    if val is not None and 10 <= float(val) <= 100:
                        return val
            for value in obj.values():
                found = find(value)
                if found is not None:
                    return found
        elif isinstance(obj, list):
            for value in obj:
                found = find(value)
                if found is not None:
                    return found
        return None

    return {"vo2_max": find(latest)}


def _timestamp_seconds(value: Any) -> datetime | None:
    n = _number(value)
    if n is None:
        return None
    try:
        return datetime.fromtimestamp(float(n), tz=timezone.utc)
    except (ValueError, OSError, OverflowError):
        return None


def _number(value: Any) -> float | int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            f = float(value)
            return int(f) if f.is_integer() else f
        except ValueError:
            return None
    return None


def _percent(value: Any, goal: Any) -> float | None:
    v = _number(value)
    g = _number(goal)
    if v is None or g is None or float(g) <= 0:
        return None
    return round(float(v) / float(g) * 100.0, 1)
