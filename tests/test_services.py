from dataclasses import dataclass
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
