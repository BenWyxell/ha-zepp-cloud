from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import (
    ZeppApiClient,
    ZeppApiError,
    ZeppAuthError,
    ZeppInvalidHostError,
    normalize_host,
)
from .const import (
    CONF_APP_TOKEN,
    CONF_HOST,
    CONF_LOOKBACK_DAYS,
    CONF_NAME,
    CONF_UPDATE_INTERVAL,
    CONF_USER_ID,
    DEFAULT_LOOKBACK_DAYS,
    DEFAULT_NAME,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MAX_LOOKBACK_DAYS,
    MAX_UPDATE_INTERVAL,
    MIN_LOOKBACK_DAYS,
    MIN_UPDATE_INTERVAL,
)


TOKEN_SELECTOR = TextSelector(
    TextSelectorConfig(type=TextSelectorType.PASSWORD)
)


class ZeppCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                user_input[CONF_HOST] = normalize_host(user_input[CONF_HOST])
                await self._validate(
                    user_input[CONF_APP_TOKEN],
                    str(user_input[CONF_USER_ID]),
                    user_input[CONF_HOST],
                )
            except ZeppInvalidHostError:
                errors["host"] = "invalid_host"
            except ZeppAuthError:
                errors["base"] = "invalid_auth"
            except ZeppApiError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(str(user_input[CONF_USER_ID]))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self._user_schema(user_input),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]):
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ):
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        if entry is None:
            return self.async_abort(reason="reauth_failed")

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await self._validate(
                    user_input[CONF_APP_TOKEN],
                    str(entry.data[CONF_USER_ID]),
                    entry.data[CONF_HOST],
                )
            except ZeppAuthError:
                errors["base"] = "invalid_auth"
            except ZeppApiError:
                errors["base"] = "cannot_connect"
            else:
                self.hass.config_entries.async_update_entry(
                    entry,
                    data={**entry.data, CONF_APP_TOKEN: user_input[CONF_APP_TOKEN]},
                )
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {vol.Required(CONF_APP_TOKEN): TOKEN_SELECTOR}
            ),
            errors=errors,
        )

    async def _validate(self, token: str, user_id: str, host: str) -> None:
        client = ZeppApiClient(
            async_get_clientsession(self.hass),
            token,
            user_id,
            host,
        )
        await client.validate()

    @staticmethod
    def _user_schema(user_input: dict[str, Any] | None) -> vol.Schema:
        values = user_input or {}
        schema: dict[Any, Any] = {
            vol.Required(
                CONF_NAME,
                default=values.get(CONF_NAME, DEFAULT_NAME),
            ): str,
            vol.Required(CONF_APP_TOKEN): TOKEN_SELECTOR,
            vol.Required(
                CONF_USER_ID,
                default=values.get(CONF_USER_ID, ""),
            ): str,
            vol.Required(
                CONF_HOST,
                default=values.get(CONF_HOST, ""),
            ): str,
            vol.Required(
                CONF_UPDATE_INTERVAL,
                default=values.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
            ): vol.All(
                vol.Coerce(int),
                vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
            ),
        }
        return vol.Schema(schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ZeppCloudOptionsFlow(config_entry)


class ZeppCloudOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry) -> None:
        self._entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = int(
            self._entry.options.get(
                CONF_UPDATE_INTERVAL,
                self._entry.data.get(
                    CONF_UPDATE_INTERVAL,
                    DEFAULT_UPDATE_INTERVAL,
                ),
            )
        )
        current_lookback = int(
            self._entry.options.get(
                CONF_LOOKBACK_DAYS,
                DEFAULT_LOOKBACK_DAYS,
            )
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_INTERVAL,
                        default=current_interval,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=MIN_UPDATE_INTERVAL,
                            max=MAX_UPDATE_INTERVAL,
                        ),
                    ),
                    vol.Required(
                        CONF_LOOKBACK_DAYS,
                        default=current_lookback,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=MIN_LOOKBACK_DAYS,
                            max=MAX_LOOKBACK_DAYS,
                        ),
                    ),
                }
            ),
        )
