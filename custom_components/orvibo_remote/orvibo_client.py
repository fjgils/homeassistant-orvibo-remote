"""Protocol/client wrapper for Orvibo devices."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from .const import MODEL_ALLONE, MODEL_ALLONE_PRO, MODEL_AUTO
from .orvibo.orvibo import Orvibo, OrviboException

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class OrviboCapabilities:
    """Detected capabilities for an Orvibo device."""

    model: str
    ir_supported: bool
    rf_supported: bool
    hardware_type: str


@dataclass(slots=True)
class OrviboDeviceInfo:
    """Discovered Orvibo device metadata."""

    host: str
    mac_hex: str
    hardware_type: str


class OrviboClient:
    """Async wrapper over vendored protocol implementation."""

    def __init__(self, host: str, model_hint: str = MODEL_AUTO, enable_rf: bool = True) -> None:
        self._host = host
        self._model_hint = model_hint
        self._enable_rf = enable_rf
        self._device: Orvibo | None = None
        self._lock = asyncio.Lock()

    @property
    def host(self) -> str:
        return self._host

    @property
    def model_hint(self) -> str:
        return self._model_hint

    @property
    def enable_rf(self) -> bool:
        return self._enable_rf

    @property
    def device(self) -> Orvibo:
        if self._device is None:
            raise OrviboException("Orvibo device is not connected")
        return self._device

    @staticmethod
    async def discover(host: str) -> OrviboDeviceInfo:
        device = await asyncio.to_thread(Orvibo.discover, host)
        if not isinstance(device, Orvibo):
            raise OrviboException(f"Unable to discover Orvibo on host {host}")
        mac = ""
        if device.mac is not None:
            mac = device.mac.hex()
        return OrviboDeviceInfo(host=host, mac_hex=mac, hardware_type=device.type)

    @staticmethod
    def detect_capabilities(hardware_type: str, model_hint: str, enable_rf: bool) -> OrviboCapabilities:
        if hardware_type == Orvibo.TYPE_SOCKET:
            return OrviboCapabilities(
                model="socket",
                ir_supported=False,
                rf_supported=False,
                hardware_type=hardware_type,
            )

        if model_hint == MODEL_ALLONE_PRO:
            model = MODEL_ALLONE_PRO
        elif model_hint == MODEL_ALLONE:
            model = MODEL_ALLONE
        else:
            model = MODEL_ALLONE_PRO if enable_rf else MODEL_ALLONE

        return OrviboCapabilities(
            model=model,
            ir_supported=True,
            rf_supported=enable_rf,
            hardware_type=hardware_type,
        )

    async def async_connect(self) -> None:
        async with self._lock:
            if self._device is not None:
                return
            self._device = await asyncio.to_thread(Orvibo.discover, self._host)

    async def async_subscribe(self) -> bool:
        await self.async_connect()
        response = await asyncio.to_thread(self.device.subscribe)
        return response is not None

    async def async_send_ir(self, code: bytes) -> bool:
        await self.async_connect()
        return bool(await asyncio.to_thread(self.device.emit_ir, code))

    async def async_learn_ir(self, timeout: int) -> bytes | None:
        await self.async_connect()
        return await asyncio.to_thread(self.device.learn, None, timeout)

    async def async_learn_rf(self) -> bytes:
        await self.async_connect()
        result = await asyncio.to_thread(self.device.learn_rf433, None)
        if not isinstance(result, (bytes, bytearray)):
            raise OrviboException("RF learn returned invalid response")
        return bytes(result)

    async def async_send_rf(self, key: bytes, state: bool = True) -> None:
        await self.async_connect()
        if not hasattr(self.device, "_learn_emit_rf433"):
            raise OrviboException("RF send not supported by protocol backend")
        await asyncio.to_thread(self.device.emit_ir, b" ")
        await asyncio.to_thread(self.device._learn_emit_rf433, 1 if state else 0, key)

    async def async_close(self) -> None:
        async with self._lock:
            if self._device is None:
                return
            try:
                await asyncio.to_thread(self._device.close)
            except Exception:  # noqa: BLE001
                _LOGGER.debug("Error closing Orvibo connection", exc_info=True)
            self._device = None
