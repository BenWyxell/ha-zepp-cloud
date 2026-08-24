from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import logging
from typing import Any
from zoneinfo import ZoneInfo

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ZeppApiClient, ZeppAuthError
from .const import (
    CONF_APP_TOKEN,
    CONF_HOST,
    CONF_LOOKBACK_DAYS,
    CONF_UPDATE_INTERVAL,
    CONF_USER_ID,
    DEFAULT_LOOKBACK_DAYS,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)
from .parser import (
    parse_band_data,
    parse_daily_health,
    parse_spo2,
    parse_stress,
    parse_training_load,
    parse_vo2,
)

_LOGGER = logging.getLogger(__name__)


class ZeppCloudCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        interval = int(
            entry.options.get(
                CONF_UPDATE_INTERVAL,
                entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
            )
        )
        self.lookback_days = int(
            entry.options.get(CONF_LOOKBACK_DAYS, DEFAULT_LOOKBACK_DAYS)
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(minutes=max(1, interval)),
        )

        self.client = ZeppApiClient(
            async_get_clientsession(hass),
            entry.data[CONF_APP_TOKEN],
            str(entry.data[CONF_USER_ID]),
            entry.data[CONF_HOST],
        )
        self._cache: dict[str, Any] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        local_today = datetime.now(ZoneInfo(self.hass.config.time_zone)).date()
        band_start = local_today - timedelta(days=max(1, self.lookback_days - 1))
        band_end = local_today

        event_days = max(7, self.lookback_days)
        from_ms = int((now - timedelta(days=event_days)).timestamp() * 1000)
        to_ms = int(now.timestamp() * 1000)
        stats_start = (now - timedelta(days=30)).date()
        stats_end = now.date()

        calls = {
            "band": self.client.band_data(band_start, band_end),
            "daily": self.client.events(
                "DailyHealth", "summary", from_ms, to_ms, limit=100
            ),
            "stress": self.client.user_events(
                "all_day_stress", from_ms, to_ms, limit=100
            ),
            "spo2": self.client.user_events(
                "blood_oxygen", from_ms, to_ms, limit=1000
            ),
            "load": self.client.sport_load(stats_start, stats_end),
            "vo2": self.client.vo2_max(stats_start, stats_end),
        }

        results = await asyncio.gather(*calls.values(), return_exceptions=True)

        failures: list[str] = []
        for key, result in zip(calls, results):
            if isinstance(result, ZeppAuthError):
                raise ConfigEntryAuthFailed("Zepp token rejected or expired.") from result
            if isinstance(result, Exception):
                failures.append(key)
                _LOGGER.warning(
                    "Zepp Cloud endpoint '%s' failed (%s).",
                    key,
                    result.__class__.__name__,
                )
                continue
            self._cache[key] = result

        if len(failures) == len(calls) and not self._cache:
            raise UpdateFailed("No Zepp Cloud endpoint returned usable data.")

        data: dict[str, Any] = {}
        data.update(parse_band_data(self._cache.get("band"), self.hass.config.time_zone))
        daily = parse_daily_health(self._cache.get("daily"))
        data.update(daily)
        data.update(parse_stress(self._cache.get("stress")))
        data.update(parse_spo2(self._cache.get("spo2")))
        data.update(parse_training_load(self._cache.get("load")))
        data.update(parse_vo2(self._cache.get("vo2")))

        if daily.get("steps") is not None:
            data["steps"] = daily["steps"]

        data["cloud_checked_at"] = now
        data["endpoint_failures"] = len(failures)
        data["failed_endpoints"] = failures

        hr_time = data.get("heart_rate_time")
        if isinstance(hr_time, datetime):
            age = max(
                0,
                (now - hr_time.astimezone(timezone.utc)).total_seconds() / 60,
            )
            data["heart_rate_age_min"] = round(age, 1)
        else:
            data["heart_rate_age_min"] = None

        return data
