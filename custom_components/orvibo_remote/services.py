"""Service handlers for Orvibo Remote."""

from __future__ import annotations

from base64 import b64decode

import voluptuous as vol

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_CODE,
    CONF_CODE_NAME,
    CONF_ENTRY_ID,
    CONF_LEGACY_STATE,
    CONF_PROTOCOL,
    CONF_TIMEOUT,
    DATA_CLIENTS,
    DATA_SERVICES_REGISTERED,
    DATA_STORES,
    LEGACY_SERVICE_EMIT,
    LEGACY_SERVICE_LEARN,
    PROTOCOL_IR,
    PROTOCOL_RF,
    SERVICE_DELETE_CODE,
    SERVICE_LEARN_IR,
    SERVICE_LEARN_RF,
    SERVICE_LIST_CODES,
    SERVICE_SEND_IR,
    SERVICE_SEND_RF,
)


SERVICE_TARGET_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_ENTRY_ID): cv.string,
        vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
    }
)


def _decode_code(raw_code: str | bytes | bytearray) -> bytes:
    if isinstance(raw_code, bytes):
        return raw_code
    if isinstance(raw_code, bytearray):
        return bytes(raw_code)
    if isinstance(raw_code, str) and raw_code.startswith("b64:"):
        return b64decode(raw_code[4:])
    if isinstance(raw_code, str):
        return b64decode(raw_code)
    raise ValueError("Unsupported code format")


def _resolve_entry_id(hass: HomeAssistant, call: ServiceCall) -> str:
    if entry_id := call.data.get(CONF_ENTRY_ID):
        return entry_id

    clients = hass.data.get(DATA_CLIENTS, {})
    if len(clients) == 1:
        return next(iter(clients))

    raise ValueError("entry_id is required when multiple devices are configured")


async def async_register_services(hass: HomeAssistant) -> None:
    if hass.data.get(DATA_SERVICES_REGISTERED):
        return

    async def _learn(call: ServiceCall, protocol: str) -> None:
        entry_id = _resolve_entry_id(hass, call)
        clients = hass.data[DATA_CLIENTS]
        stores = hass.data[DATA_STORES]
        client = clients[entry_id]
        store = stores[entry_id]
        code_name = call.data[CONF_CODE_NAME]

        if protocol == PROTOCOL_IR:
            timeout = int(call.data.get(CONF_TIMEOUT, 15))
            raw = await client.async_learn_ir(timeout)
            if raw is None:
                raise ValueError("No IR signal captured")
        else:
            raw = await client.async_learn_rf()

        await store.save_code(protocol, code_name, raw)

    async def _send(call: ServiceCall, protocol: str) -> None:
        entry_id = _resolve_entry_id(hass, call)
        clients = hass.data[DATA_CLIENTS]
        stores = hass.data[DATA_STORES]
        client = clients[entry_id]
        store = stores[entry_id]

        code = call.data.get(CONF_CODE)
        if code is None:
            code_name = call.data[CONF_CODE_NAME]
            stored = await store.get_code(protocol, code_name)
            if stored is None:
                raise ValueError(f"Code '{code_name}' not found")
            payload = stored
        else:
            payload = _decode_code(code)

        if protocol == PROTOCOL_IR:
            result = await client.async_send_ir(payload)
            if not result:
                raise ValueError("IR send failed")
        else:
            state = bool(call.data.get(CONF_LEGACY_STATE, True))
            await client.async_send_rf(payload, state=state)

    async def _list_codes(call: ServiceCall) -> None:
        entry_id = _resolve_entry_id(hass, call)
        protocol = call.data.get(CONF_PROTOCOL)
        store = hass.data[DATA_STORES][entry_id]
        codes = await store.list_codes(protocol=protocol)
        hass.states.async_set(
            f"orvibo_remote.codes_{entry_id}",
            len(codes),
            {"entry_id": entry_id, "codes": codes},
        )

    async def _delete_code(call: ServiceCall) -> None:
        entry_id = _resolve_entry_id(hass, call)
        protocol = call.data[CONF_PROTOCOL]
        code_name = call.data[CONF_CODE_NAME]
        store = hass.data[DATA_STORES][entry_id]
        deleted = await store.delete_code(protocol=protocol, name=code_name)
        if not deleted:
            raise ValueError(f"Code '{code_name}' not found")

    hass.services.async_register(
        "orvibo_remote",
        SERVICE_LEARN_IR,
        lambda call: _learn(call, PROTOCOL_IR),
        schema=SERVICE_TARGET_SCHEMA.extend(
            {
                vol.Required(CONF_CODE_NAME): cv.string,
                vol.Optional(CONF_TIMEOUT, default=15): vol.Coerce(int),
            }
        ),
    )
    hass.services.async_register(
        "orvibo_remote",
        SERVICE_SEND_IR,
        lambda call: _send(call, PROTOCOL_IR),
        schema=SERVICE_TARGET_SCHEMA.extend(
            {
                vol.Optional(CONF_CODE_NAME): cv.string,
                vol.Optional(CONF_CODE): vol.Any(cv.string, bytes, bytearray),
            }
        ),
    )
    hass.services.async_register(
        "orvibo_remote",
        SERVICE_LEARN_RF,
        lambda call: _learn(call, PROTOCOL_RF),
        schema=SERVICE_TARGET_SCHEMA.extend({vol.Required(CONF_CODE_NAME): cv.string}),
    )
    hass.services.async_register(
        "orvibo_remote",
        SERVICE_SEND_RF,
        lambda call: _send(call, PROTOCOL_RF),
        schema=SERVICE_TARGET_SCHEMA.extend(
            {
                vol.Optional(CONF_CODE_NAME): cv.string,
                vol.Optional(CONF_CODE): vol.Any(cv.string, bytes, bytearray),
                vol.Optional(CONF_LEGACY_STATE, default=True): cv.boolean,
            }
        ),
    )
    hass.services.async_register(
        "orvibo_remote",
        SERVICE_LIST_CODES,
        _list_codes,
        schema=SERVICE_TARGET_SCHEMA.extend(
            {vol.Optional(CONF_PROTOCOL): vol.In([PROTOCOL_IR, PROTOCOL_RF])}
        ),
    )
    hass.services.async_register(
        "orvibo_remote",
        SERVICE_DELETE_CODE,
        _delete_code,
        schema=SERVICE_TARGET_SCHEMA.extend(
            {
                vol.Required(CONF_PROTOCOL): vol.In([PROTOCOL_IR, PROTOCOL_RF]),
                vol.Required(CONF_CODE_NAME): cv.string,
            }
        ),
    )

    hass.services.async_register(
        "orvibo_remote",
        LEGACY_SERVICE_LEARN,
        lambda call: _learn(call, PROTOCOL_IR),
        schema=SERVICE_TARGET_SCHEMA.extend(
            {
                vol.Required(CONF_CODE_NAME): cv.string,
                vol.Optional(CONF_TIMEOUT, default=15): vol.Coerce(int),
            }
        ),
    )
    hass.services.async_register(
        "orvibo_remote",
        LEGACY_SERVICE_EMIT,
        lambda call: _send(call, PROTOCOL_IR),
        schema=SERVICE_TARGET_SCHEMA.extend(
            {
                vol.Optional(CONF_CODE_NAME): cv.string,
                vol.Optional(CONF_CODE): vol.Any(cv.string, bytes, bytearray),
            }
        ),
    )

    hass.data[DATA_SERVICES_REGISTERED] = True
