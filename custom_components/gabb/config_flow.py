"""Config flow for the Gabb integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
    OptionsFlowWithConfigEntry,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback

from .api import GabbAPI
from .const import CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, DOMAIN, MIN_UPDATE_INTERVAL
from .exceptions import GabbAuthError, GabbConnectionError

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def _validate_credentials(username: str, password: str) -> None:
    """Validate credentials by logging in and fetching locations."""
    session = aiohttp.ClientSession()
    api = GabbAPI(session, username, password)
    try:
        await api.login()
        await api.get_locations()
    finally:
        await session.close()


class GabbConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gabb."""

    VERSION = 1

    _reauth_entry_data: dict[str, Any] | None = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: Any) -> OptionsFlow:
        """Get the options flow handler."""
        return GabbOptionsFlow(config_entry)

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial user step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME].strip().lower()
            password = user_input[CONF_PASSWORD]

            await self.async_set_unique_id(username)
            self._abort_if_unique_id_configured()

            try:
                await _validate_credentials(username, password)
            except GabbAuthError:
                errors["base"] = "invalid_auth"
            except GabbConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during Gabb config flow")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=username,
                    data={
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self,
        entry_data: dict[str, Any],
    ) -> ConfigFlowResult:
        """Handle reauth when credentials expire."""
        self._reauth_entry_data = dict(entry_data)
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle reauth confirmation."""
        errors: dict[str, str] = {}

        if user_input is not None:
            assert self._reauth_entry_data is not None
            username = self._reauth_entry_data[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            try:
                await _validate_credentials(username, password)
            except GabbAuthError:
                errors["base"] = "invalid_auth"
            except GabbConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during Gabb reauth")
                errors["base"] = "unknown"
            else:
                entry = self.hass.config_entries.async_get_entry(
                    self.context["entry_id"]
                )
                if entry:
                    self.hass.config_entries.async_update_entry(
                        entry,
                        data={
                            CONF_USERNAME: username,
                            CONF_PASSWORD: password,
                        },
                    )
                    await self.hass.config_entries.async_reload(entry.entry_id)
                    return self.async_abort(reason="reauth_successful")
                return self.async_abort(reason="unknown")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {vol.Required(CONF_PASSWORD): str}
            ),
            errors=errors,
            description_placeholders={
                "username": (self._reauth_entry_data or {}).get(CONF_USERNAME, ""),
            },
        )


class GabbOptionsFlow(OptionsFlowWithConfigEntry):
    """Handle Gabb options."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.options.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
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
                        vol.Range(min=MIN_UPDATE_INTERVAL),
                    ),
                }
            ),
        )
