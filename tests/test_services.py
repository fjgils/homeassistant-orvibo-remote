from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.orvibo_remote.const import (
    CONF_CODE,
    CONF_CODE_NAME,
    CONF_ENTRY_ID,
    DATA_CLIENTS,
    DATA_STORES,
    PROTOCOL_IR,
    PROTOCOL_RF,
    SERVICE_LEARN_IR,
    SERVICE_SEND_IR,
)
from custom_components.orvibo_remote import services
from custom_components.orvibo_remote.services import async_register_services


@dataclass
class Call:
    data: dict


class FakeServices:
    def __init__(self) -> None:
        self.handlers = {}

    def async_register(self, domain, service, handler, schema=None) -> None:
        self.handlers[f"{domain}.{service}"] = handler


class FakeStates:
    def async_set(self, *_args, **_kwargs):
        return None


class FakeHass:
    def __init__(self) -> None:
        self.data = {
            DATA_CLIENTS: {},
            DATA_STORES: {},
        }
        self.services = FakeServices()
        self.states = FakeStates()


class FakeEntityRegistry:
    def __init__(self, entries: dict[str, str]) -> None:
        self._entries = entries

    def async_get(self, entity_id: str):
        if config_entry_id := self._entries.get(entity_id):
            return SimpleNamespace(config_entry_id=config_entry_id)
        return None


@pytest.mark.asyncio
async def test_services_learn_and_send_ir() -> None:
    hass = FakeHass()
    client = AsyncMock()
    store = AsyncMock()

    client.async_learn_ir.return_value = b"abc"
    client.async_send_ir.return_value = True
    store.get_code.return_value = b"abc"

    hass.data[DATA_CLIENTS]["entry1"] = client
    hass.data[DATA_STORES]["entry1"] = store

    await async_register_services(hass)

    learn = hass.services.handlers[f"orvibo_remote.{SERVICE_LEARN_IR}"]
    await learn(Call({CONF_ENTRY_ID: "entry1", CONF_CODE_NAME: "tv_power"}))
    store.save_code.assert_awaited_once_with(PROTOCOL_IR, "tv_power", b"abc")

    send = hass.services.handlers[f"orvibo_remote.{SERVICE_SEND_IR}"]
    await send(Call({CONF_ENTRY_ID: "entry1", CONF_CODE_NAME: "tv_power"}))
    client.async_send_ir.assert_awaited_with(b"abc")


@pytest.mark.asyncio
async def test_service_delete_code_missing_raises() -> None:
    hass = FakeHass()
    client = AsyncMock()
    store = AsyncMock()
    store.delete_code.return_value = False

    hass.data[DATA_CLIENTS]["entry1"] = client
    hass.data[DATA_STORES]["entry1"] = store

    await async_register_services(hass)
    delete = hass.services.handlers["orvibo_remote.delete_code"]

    with pytest.raises(ValueError):
        await delete(
            Call(
                {
                    CONF_ENTRY_ID: "entry1",
                    "protocol": PROTOCOL_RF,
                    CONF_CODE_NAME: "missing",
                }
            )
        )


@pytest.mark.asyncio
async def test_service_send_ir_from_inline_code() -> None:
    hass = FakeHass()
    client = AsyncMock()
    store = AsyncMock()
    client.async_send_ir.return_value = True

    hass.data[DATA_CLIENTS]["entry1"] = client
    hass.data[DATA_STORES]["entry1"] = store

    await async_register_services(hass)
    send = hass.services.handlers[f"orvibo_remote.{SERVICE_SEND_IR}"]
    await send(Call({CONF_ENTRY_ID: "entry1", CONF_CODE: "dGVzdA=="}))

    client.async_send_ir.assert_awaited_once_with(b"test")


@pytest.mark.asyncio
async def test_service_send_ir_missing_payload_raises() -> None:
    hass = FakeHass()
    client = AsyncMock()
    store = AsyncMock()
    hass.data[DATA_CLIENTS]["entry1"] = client
    hass.data[DATA_STORES]["entry1"] = store

    await async_register_services(hass)
    send = hass.services.handlers[f"orvibo_remote.{SERVICE_SEND_IR}"]

    with pytest.raises(ValueError, match="Either code_name or code is required"):
        await send(Call({CONF_ENTRY_ID: "entry1"}))


@pytest.mark.asyncio
async def test_service_send_ir_rejects_both_payload_sources() -> None:
    hass = FakeHass()
    client = AsyncMock()
    store = AsyncMock()
    hass.data[DATA_CLIENTS]["entry1"] = client
    hass.data[DATA_STORES]["entry1"] = store

    await async_register_services(hass)
    send = hass.services.handlers[f"orvibo_remote.{SERVICE_SEND_IR}"]

    with pytest.raises(ValueError, match="Provide either code_name or code, not both"):
        await send(
            Call(
                {
                    CONF_ENTRY_ID: "entry1",
                    CONF_CODE_NAME: "tv_power",
                    CONF_CODE: "dGVzdA==",
                }
            )
        )


@pytest.mark.asyncio
async def test_service_resolves_entry_id_from_entity_id(monkeypatch: pytest.MonkeyPatch) -> None:
    hass = FakeHass()
    client = AsyncMock()
    store = AsyncMock()
    store.get_code.return_value = b"abc"
    hass.data[DATA_CLIENTS]["entry1"] = client
    hass.data[DATA_STORES]["entry1"] = store

    monkeypatch.setattr(
        services.er,
        "async_get",
        lambda _hass: FakeEntityRegistry({"remote.orvibo": "entry1"}),
    )

    await async_register_services(hass)
    send = hass.services.handlers[f"orvibo_remote.{SERVICE_SEND_IR}"]
    await send(Call({"entity_id": ["remote.orvibo"], CONF_CODE_NAME: "tv_power"}))

    client.async_send_ir.assert_awaited_once_with(b"abc")
