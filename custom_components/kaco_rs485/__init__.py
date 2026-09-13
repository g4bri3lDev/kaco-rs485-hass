"""KACO RS485 integration."""

from __future__ import annotations

from homeassistant.const import CONF_PORT, Platform
from homeassistant.core import HomeAssistant

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

    # Registered before the first refresh so a failed setup still releases the
    # port; a second master on an RS485 bus corrupts everyone's traffic.
    entry.async_on_unload(coordinator.async_close)

    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: KacoRs485ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
