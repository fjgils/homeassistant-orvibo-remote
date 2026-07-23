"""The Orvibo Remote integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_ENABLE_RF,
    CONF_MODEL_HINT,
    DATA_CLIENTS,
    DATA_COORDINATORS,
    DATA_STORES,
    PLATFORMS,
)
from .coordinator import OrviboCoordinator
from .orvibo.orvibo import OrviboException
from .orvibo_client import OrviboClient
from .services import async_register_services
from .store import OrviboCodeStore


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DATA_CLIENTS, {})
    hass.data.setdefault(DATA_STORES, {})
    hass.data.setdefault(DATA_COORDINATORS, {})
    await async_register_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data[CONF_HOST]
    model_hint = entry.options.get(CONF_MODEL_HINT, entry.data.get(CONF_MODEL_HINT, "auto"))
    enable_rf = entry.options.get(CONF_ENABLE_RF, entry.data.get(CONF_ENABLE_RF, True))

    client = OrviboClient(host=host, model_hint=model_hint, enable_rf=enable_rf)
    try:
        await client.async_connect()
        capabilities = client.detect_capabilities(
            client.device.type, model_hint, enable_rf
        )
        coordinator = OrviboCoordinator(hass, client, capabilities)
        await coordinator.async_config_entry_first_refresh()
    except OrviboException as err:
        raise ConfigEntryNotReady(
            f"Unable to initialize Orvibo device at {host}"
        ) from err

    hass.data[DATA_CLIENTS][entry.entry_id] = client
    hass.data[DATA_STORES][entry.entry_id] = OrviboCodeStore(hass, entry.entry_id)
    hass.data[DATA_COORDINATORS][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    client = hass.data[DATA_CLIENTS].pop(entry.entry_id, None)
    hass.data[DATA_STORES].pop(entry.entry_id, None)
    hass.data[DATA_COORDINATORS].pop(entry.entry_id, None)
    if client is not None:
        await client.async_close()

    return True
