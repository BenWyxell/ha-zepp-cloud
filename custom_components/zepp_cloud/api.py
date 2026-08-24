from __future__ import annotations

import asyncio
from datetime import date
import re
from typing import Any
import uuid

from aiohttp import ClientResponseError, ClientSession


_HOST_RE = re.compile(
    r"^api-mifit(?:-[a-z0-9-]+)?(?:\.[a-z0-9-]+)*\.(?:zepp\.com|huami\.com)$",
    re.IGNORECASE,
)


class ZeppApiError(Exception):
    """Base Zepp Cloud API error."""


class ZeppAuthError(ZeppApiError):
    """Authentication error."""


class ZeppInvalidHostError(ZeppApiError):
    """Configured API host is not a Zepp/Huami API host."""


def normalize_host(value: str) -> str:
    host = value.strip().lower()
    host = host.removeprefix("https://").removeprefix("http://").rstrip("/")
    if "/" in host or ":" in host or not _HOST_RE.fullmatch(host):
        raise ZeppInvalidHostError(
            "Host must be an api-mifit Zepp/Huami hostname, without scheme or path."
        )
    return host


class ZeppApiClient:
    """Minimal async wrapper around the private Zepp/Huami API."""

    def __init__(
        self,
        session: ClientSession,
        app_token: str,
        user_id: str,
        host: str,
    ) -> None:
        self._session = session
        self._token = app_token.strip()
        self._user_id = str(user_id).strip()
        self._host = normalize_host(host)
        self._base = f"https://{self._host}"

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def host(self) -> str:
        return self._host

    @staticmethod
    def _request_id() -> str:
        return str(uuid.uuid4()).upper()

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "apptoken": self._token,
            "appname": "com.huami.midong",
            "appplatform": "ios_phone",
            "accept": "*/*",
            "v": "2.0",
            "vn": "10.2.5",
            "cv": "1722_10.2.5",
            "vb": "202604132257",
            "user-agent": "Zepp/10.2.5 (iPhone; iOS 26; Scale/3.00)",
            "lang": "en",
            "country": "",
            "timezone": "UTC",
        }

    async def _get_json(self, path: str, params: dict[str, Any]) -> Any:
        query = {"r": self._request_id(), **params}
        try:
            async with asyncio.timeout(30):
                response = await self._session.get(
                    f"{self._base}{path}",
                    params=query,
                    headers=self._headers,
                )
                if response.status in (401, 403):
                    raise ZeppAuthError(
                        f"Zepp authentication rejected (HTTP {response.status})."
                    )
                if response.status >= 400:
                    raise ZeppApiError(f"Zepp API returned HTTP {response.status}.")
                return await response.json(content_type=None)
        except ZeppAuthError:
            raise
        except ZeppApiError:
            raise
        except TimeoutError as err:
            raise ZeppApiError("Zepp API request timed out.") from err
        except ClientResponseError as err:
            raise ZeppApiError(f"Zepp API returned HTTP {err.status}.") from err
        except (OSError, ValueError) as err:
            raise ZeppApiError("Could not read a valid Zepp API response.") from err

    async def validate(self) -> None:
        from datetime import datetime, timedelta, timezone

        today = datetime.now(timezone.utc).date()
        result = await self.sport_load(today - timedelta(days=1), today)
        if not isinstance(result, dict):
            raise ZeppApiError("Unexpected Zepp API response.")

    async def band_data(self, from_date: date, to_date: date) -> Any:
        return await self._get_json(
            "/v1/data/band_data.json",
            {
                "userid": self._user_id,
                "from_date": from_date.isoformat(),
                "to_date": to_date.isoformat(),
                "query_type": "detail",
                "byteLength": 8,
                "device_type": 0,
            },
        )

    async def user_events(
        self,
        event_type: str,
        from_ms: int,
        to_ms: int,
        *,
        sub_type: str | None = None,
        limit: int = 2000,
    ) -> Any:
        params: dict[str, Any] = {
            "eventType": event_type,
            "from": from_ms,
            "to": to_ms,
            "limit": limit,
            "reverse": 0,
            "userId": self._user_id,
        }
        if sub_type:
            params["subType"] = sub_type
        return await self._get_json(f"/users/{self._user_id}/events", params)

    async def events(
        self,
        event_type: str,
        sub_type: str,
        from_ms: int,
        to_ms: int,
        *,
        limit: int = 500,
    ) -> Any:
        return await self._get_json(
            "/v2/users/me/events",
            {
                "eventType": event_type,
                "subType": sub_type,
                "from": from_ms,
                "to": to_ms,
                "limit": limit,
                "reverse": 1,
            },
        )

    async def blood_pressure(
        self,
        *,
        days: int = 7,
        to_date: date | None = None,
        source: str = "com.huami.midong.associated,com.huami.midong",
    ) -> Any:
        """Blood-pressure history from the Zepp mobile API."""
        target = to_date or date.today()
        return await self._get_json(
            "/users/me/bloodPressure",
            {
                "days": max(1, int(days)),
                "sourceArrayStr": source,
                "toDate": target.isoformat(),
            },
        )

    async def sport_load(self, start_day: date, end_day: date) -> Any:
        return await self._get_json(
            f"/v2/watch/users/{self._user_id}/WatchSportStatistics/SPORT_LOAD",
            {
                "startDay": start_day.isoformat(),
                "endDay": end_day.isoformat(),
                "limit": 900,
                "isReverse": "true",
            },
        )

    async def vo2_max(self, start_day: date, end_day: date) -> Any:
        return await self._get_json(
            f"/v2/watch/users/{self._user_id}/WatchSportStatistics/VO2_MAX",
            {
                "startDay": start_day.isoformat(),
                "endDay": end_day.isoformat(),
                "limit": 900,
                "isReverse": "true",
            },
        )
