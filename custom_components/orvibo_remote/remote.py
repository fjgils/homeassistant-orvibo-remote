"""Remote platform for Orvibo devices."""

from __future__ import annotations

import logging
from base64 import b64decode
from collections.abc import Iterable
from typing import Any

import voluptuous as vol

from homeassistant.components.remote import (
    PLATFORM_SCHEMA as REMOTE_PLATFORM_SCHEMA,
    RemoteEntity,
    RemoteEntityFeature,
)
from homeassistant.const import CONF_HOST, CONF_IP_ADDRESS, CONF_NAME, CONF_TIMEOUT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_ENABLE_RF,
    CONF_MODEL_HINT,
    DATA_CLIENTS,
    DATA_COORDINATORS,
    DEFAULT_NAME,
)
from .coordinator import OrviboCoordinator
from .orvibo.orvibo import OrviboException
from .orvibo_client import OrviboClient

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = REMOTE_PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_HOST): cv.string,
        vol.Optional(CONF_IP_ADDRESS): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_MODEL_HINT, default="auto"): cv.string,
        vol.Optional(CONF_ENABLE_RF, default=True): cv.boolean,
        vol.Optional(CONF_TIMEOUT, default=15): vol.Coerce(int),
    }
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    client: OrviboClient = hass.data[DATA_CLIENTS][config_entry.entry_id]
    coordinator: OrviboCoordinator = hass.data[DATA_COORDINATORS][config_entry.entry_id]
    name = config_entry.title
    async_add_entities(
        [OrviboRemote(name=name, client=client, timeout=15, coordinator=coordinator)]
    )


async def async_setup_platform(
    hass: HomeAssistant,
    config,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None,
) -> None:
    host = config.get(CONF_HOST) or config.get(CONF_IP_ADDRESS)
    if not host:
        _LOGGER.error("Missing host/ip_address in YAML configuration")
        return
    name = config[CONF_NAME]
    model_hint = config[CONF_MODEL_HINT]
    enable_rf = config[CONF_ENABLE_RF]
    timeout = config[CONF_TIMEOUT]

    client = OrviboClient(host=host, model_hint=model_hint, enable_rf=enable_rf)
    try:
        await client.async_connect()
    except OrviboException:
        _LOGGER.exception("Unable to discover AllOne device at %s", host)
        return

    async_add_entities([OrviboRemote(name=name, client=client, timeout=timeout)])


class OrviboRemote(RemoteEntity):
    """Representation of an Orvibo remote entity."""

    _attr_should_poll = False

    def __init__(
        self,
        name: str,
        client: OrviboClient,
        timeout: int = 15,
        coordinator: OrviboCoordinator | None = None,
    ) -> None:
        self._attr_name = name
        self._client = client
        self._timeout = timeout
        self._coordinator = coordinator
        self._attr_unique_id = f"orvibo-{client.host}"
        self._attr_supported_features = RemoteEntityFeature.LEARN_COMMAND

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        capabilities = self._client.detect_capabilities(
            hardware_type="irda",
            model_hint=self._client.model_hint,
            enable_rf=self._client.enable_rf,
        )
        return {
            "host": self._client.host,
            "model": capabilities.model,
            "ir_supported": capabilities.ir_supported,
            "rf_supported": capabilities.rf_supported,
        }

    @property
    def available(self) -> bool:
        if self._coordinator is None:
            return True
        return bool(self._coordinator.data and self._coordinator.data.get("available"))

    def _decode_command(self, command: str | bytes | bytearray) -> bytes:
        if isinstance(command, str):
            if command.startswith("b64:"):
                return b64decode(command[4:])
            return b64decode(command)

        if isinstance(command, bytearray):
            return bytes(command)

        if isinstance(command, bytes):
            return command

        raise ValueError("Unable to decode command")

    async def async_send_command(
        self,
        command: Iterable[str | bytes],
        **kwargs: Any,
    ) -> None:
        if command is None:
            _LOGGER.debug("No command provided to send")
            return

        for encoded_command in command:
            raw_command = self._decode_command(encoded_command)
            _LOGGER.debug("Sending IR command (%s bytes)", len(raw_command))
            result = await self._client.async_send_ir(raw_command)
            if not result:
                raise RuntimeError("IR send failed")

    async def async_learn_command(self, **kwargs: Any) -> None:
        timeout = int(kwargs.get(CONF_TIMEOUT, self._timeout))
        signal = await self._client.async_learn_ir(timeout)
        if signal is None:
            raise RuntimeError("No IR signal captured")
