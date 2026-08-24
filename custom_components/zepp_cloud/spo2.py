from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _number(value: Any) -> float | int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            number = float(value)
            return int(number) if number.is_integer() else number
        except ValueError:
            return None
    return None


def parse_spo2_v2(payload: Any) -> dict[str, Any]:
    """Parse Zepp Spo2V2/real_data cloud events.

    Observed payload shape:
      value.startTime: millisecond base timestamp
      value.samples[].spo2: final saturation percentage
      value.samples[].s: measurement-start offset in milliseconds
      value.samples[].u: measurement-finish offset in milliseconds

    The finish offset is preferred for the sensor timestamp because the SpO2
    value is considered complete at that point. The start offset and event
    timestamp are used as fallbacks.
    """
    out: dict[str, Any] = {
        "spo2": None,
        "spo2_time": None,
        "spo2_auto": None,
        "spo2_samples": 0,
    }

    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        return out

    points: list[tuple[int, float, bool | None]] = []

    for item in payload["items"]:
        if not isinstance(item, dict):
            continue
        value = item.get("value")
        if not isinstance(value, dict):
            continue
        samples = value.get("samples")
        if not isinstance(samples, list):
            continue

        base_ms = _number(value.get("startTime"))
        event_ms = _number(item.get("timestamp"))

        for sample in samples:
            if not isinstance(sample, dict):
                continue

            spo2 = _number(sample.get("spo2"))
            if spo2 is None or not 50 <= float(spo2) <= 100:
                continue

            timestamp_ms: int | None = None
            if base_ms is not None:
                offset = _number(sample.get("u"))
                if offset is None:
                    offset = _number(sample.get("s"))
                timestamp_ms = int(float(base_ms) + float(offset or 0))
            elif event_ms is not None:
                timestamp_ms = int(event_ms)

            is_auto = sample.get("isAuto")
            auto = is_auto if isinstance(is_auto, bool) else None
            points.append((timestamp_ms or 0, float(spo2), auto))

    if not points:
        return out

    points.sort(key=lambda point: point[0])
    timestamp_ms, spo2, auto = points[-1]

    out["spo2"] = int(spo2) if spo2.is_integer() else spo2
    out["spo2_time"] = (
        datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
        if timestamp_ms
        else None
    )
    out["spo2_auto"] = auto
    out["spo2_samples"] = len(points)
    return out
