"""KACO RS485 integration."""

from __future__ import annotations

from homeassistant.const import CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from kaco_rs485 import BusError

from .const import CONF_ADDRESSES
from .coordinator import KacoRs485ConfigEntry, KacoRs485Coordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: KacoRs485ConfigEntry) -> bool:
    coordinator = KacoRs485Coordinator(
        hass,
        entry,
        port=entry.data[CONF_PORT],
        addresses=entry.data[CONF_ADDRESSES],
    )

    try:
        await coordinator.async_open()
    except BusError as err:
        raise ConfigEntryNotReady(f"Cannot open {entry.data[CONF_PORT]}: {err}") from err

    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: KacoRs485ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_close()
    return unloaded
