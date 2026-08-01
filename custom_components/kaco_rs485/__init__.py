"""KACO RS485 integration."""

from __future__ import annotations

from homeassistant.const import CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from kaco_rs485 import BusError

from .const import CONF_ADDRESSES, DOMAIN, MANUFACTURER
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

    # The bus itself, so the inverters have something to hang off. Several
    # inverters share one port, and a port that disappears should degrade in
    # one place rather than as several unrelated failures.
    dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name="KACO RS485 bus",
        manufacturer=MANUFACTURER,
        model=entry.data[CONF_PORT],
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: KacoRs485ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_close()
    return unloaded
