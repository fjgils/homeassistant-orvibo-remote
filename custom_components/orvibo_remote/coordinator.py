"""Coordinator for Orvibo state and reachability."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_TIMEOUT
from .orvibo_client import OrviboCapabilities, OrviboClient


class OrviboCoordinator(DataUpdateCoordinator[dict[str, bool]]):
    """Runtime coordinator for a single Orvibo device."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: OrviboClient,
        capabilities: OrviboCapabilities,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        super().__init__(
            hass,
            logger=logging.getLogger(__name__),
            name=f"orvibo_{client.host}",
            update_interval=timedelta(seconds=60),
        )
        self.client = client
        self.capabilities = capabilities
        self.timeout = timeout

    async def _async_update_data(self) -> dict[str, bool]:
        try:
            subscribed = await self.client.async_subscribe()
            return {"available": subscribed}
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Unable to refresh Orvibo state: {err}") from err
