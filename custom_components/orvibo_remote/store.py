"""Persistent code store for Orvibo IR/RF payloads."""

from __future__ import annotations

import base64
from collections.abc import Mapping

from homeassistant.helpers.storage import Store

from .const import PROTOCOL_IR, PROTOCOL_RF, STORAGE_KEY, STORAGE_VERSION


class OrviboCodeStore:
    """Storage abstraction used by services and entities."""

    def __init__(self, hass, entry_id: str) -> None:
        self._entry_id = entry_id
        self._store = Store[dict](hass, STORAGE_VERSION, STORAGE_KEY)

    async def _load(self) -> dict:
        data = await self._store.async_load() or {}
        entries = data.setdefault("entries", {})
        entry = entries.setdefault(self._entry_id, {})
        entry.setdefault(PROTOCOL_IR, {})
        entry.setdefault(PROTOCOL_RF, {})
        return data

    async def list_codes(self, protocol: str | None = None) -> dict[str, str]:
        data = await self._load()
        entry = data["entries"][self._entry_id]
        if protocol:
            return dict(entry.get(protocol, {}))

        merged: dict[str, str] = {}
        for proto in (PROTOCOL_IR, PROTOCOL_RF):
            for name, value in entry.get(proto, {}).items():
                merged[f"{proto}:{name}"] = value
        return merged

    async def save_code(self, protocol: str, name: str, raw_code: bytes) -> None:
        data = await self._load()
        encoded = base64.b64encode(raw_code).decode("ascii")
        data["entries"][self._entry_id][protocol][name] = encoded
        await self._store.async_save(data)

    async def get_code(self, protocol: str, name: str) -> bytes | None:
        data = await self._load()
        entry = data["entries"][self._entry_id][protocol]
        if name not in entry:
            return None
        return base64.b64decode(entry[name])

    async def delete_code(self, protocol: str, name: str) -> bool:
        data = await self._load()
        section: Mapping[str, str] = data["entries"][self._entry_id][protocol]
        if name not in section:
            return False
        del data["entries"][self._entry_id][protocol][name]
        await self._store.async_save(data)
        return True
