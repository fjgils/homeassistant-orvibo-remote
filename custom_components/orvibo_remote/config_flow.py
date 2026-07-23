"""Config flow for Orvibo Remote."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME

from .const import (
    CONF_ENABLE_RF,
    CONF_MODEL_HINT,
    DEFAULT_NAME,
    MODEL_AUTO,
    SUPPORTED_MODEL_HINTS,
)
from .orvibo.orvibo import OrviboException
from .orvibo_client import OrviboClient


class OrviboRemoteConfigFlow(config_entries.ConfigFlow, domain="orvibo_remote"):
    """Handle a config flow for Orvibo Remote."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            try:
                await OrviboClient.discover(host)
            except OrviboException:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, host),
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Optional(CONF_MODEL_HINT, default=MODEL_AUTO): vol.In(
                    SUPPORTED_MODEL_HINTS
                ),
                vol.Optional(CONF_ENABLE_RF, default=True): bool,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry):
        return OrviboRemoteOptionsFlow(config_entry)


class OrviboRemoteOptionsFlow(config_entries.OptionsFlow):
    """Orvibo options flow."""

    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = self._config_entry.data
        options = self._config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_MODEL_HINT,
                    default=options.get(CONF_MODEL_HINT, data.get(CONF_MODEL_HINT, MODEL_AUTO)),
                ): vol.In(SUPPORTED_MODEL_HINTS),
                vol.Optional(
                    CONF_ENABLE_RF,
                    default=options.get(CONF_ENABLE_RF, data.get(CONF_ENABLE_RF, True)),
                ): bool,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
