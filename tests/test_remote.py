from unittest.mock import AsyncMock

import pytest

from custom_components.orvibo_remote.remote import OrviboRemote


@pytest.mark.asyncio
async def test_async_send_command_decodes_b64() -> None:
    client = AsyncMock()
    client.host = "127.0.0.1"
    client.model_hint = "auto"
    client.enable_rf = True
    client.detect_capabilities.return_value.model = "allone_pro"
    client.detect_capabilities.return_value.ir_supported = True
    client.detect_capabilities.return_value.rf_supported = True
    client.async_send_ir.return_value = True

    entity = OrviboRemote("Test", client)
    await entity.async_send_command(["b64:dGVzdA=="])

    client.async_send_ir.assert_awaited_once_with(b"test")


@pytest.mark.asyncio
async def test_async_send_command_raw_bytes() -> None:
    client = AsyncMock()
    client.host = "127.0.0.1"
    client.model_hint = "auto"
    client.enable_rf = True
    client.detect_capabilities.return_value.model = "allone"
    client.detect_capabilities.return_value.ir_supported = True
    client.detect_capabilities.return_value.rf_supported = False
    client.async_send_ir.return_value = True

    entity = OrviboRemote("Test", client)
    payload = b"raw"
    await entity.async_send_command([payload])

    client.async_send_ir.assert_awaited_once_with(payload)
