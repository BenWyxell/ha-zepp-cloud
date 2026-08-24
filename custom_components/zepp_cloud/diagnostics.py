from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_HOST,
    CONF_LOOKBACK_DAYS,
    CONF_NAME,
    CONF_UPDATE_INTERVAL,
    DEFAULT_LOOKBACK_DAYS,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return deliberately privacy-minimal diagnostics.

    Do not include token, Zepp user ID, or health measurements.
    """
    coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}

    return {
        "integration": {
            "name": entry.data.get(CONF_NAME),
            "host": entry.data.get(CONF_HOST),
            "update_interval_minutes": entry.options.get(
                CONF_UPDATE_INTERVAL,
                entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
            ),
            "lookback_days": entry.options.get(
                CONF_LOOKBACK_DAYS,
                DEFAULT_LOOKBACK_DAYS,
            ),
        },
        "status": {
            "last_update_success": coordinator.last_update_success,
            "endpoint_failures": data.get("endpoint_failures"),
            "failed_endpoints": data.get("failed_endpoints"),
            "has_heart_rate": data.get("heart_rate") is not None,
            "has_sleep": data.get("sleep_score") is not None,
            "has_stress": data.get("stress") is not None,
            "has_spo2": data.get("spo2") is not None,
            "has_vo2_max": data.get("vo2_max") is not None,
        },
        "privacy_note": (
            "Token, user ID, raw health values and historical health payloads "
            "are intentionally excluded."
        ),
    }
