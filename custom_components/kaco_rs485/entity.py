"""Shared entity base.

One Home Assistant device per inverter.
"""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from kaco_rs485 import InverterState

from .const import CONF_INVERTERS, DOMAIN, MANUFACTURER, SERIES_PREFIX
from .coordinator import KacoRs485Coordinator


class KacoRs485Entity(CoordinatorEntity[KacoRs485Coordinator]):
    """Base for every entity belonging to one inverter."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: KacoRs485Coordinator, address: int) -> None:
        super().__init__(coordinator)
        self._address = address

        entry = coordinator.config_entry
        # From the entry, not the current poll: these inverters stop answering
        # once the sun is down, and a device restarted at night must not lose
        # its name and model until morning.
        inverter_type = entry.data.get(CONF_INVERTERS, {}).get(str(address))

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}_{address}")},
            name=self._device_name(address, inverter_type),
            manufacturer=MANUFACTURER,
            model=inverter_type,
        )

    @staticmethod
    def _device_name(address: int, inverter_type: str | None) -> str:
        """e.g. `"KACO Powador 6400xi (1)"`.

        The address is always appended, never only when two units collide: it
        is the only unique identifier these inverters expose, since command `s`
        returns zero bytes on xi hardware, and it is set on the front panel so
        the name maps to something you can walk up to and read.
        """
        if not inverter_type:
            return f"Inverter {address}"
        return f"{SERIES_PREFIX} {inverter_type} ({address})"

    @property
    def inverter(self) -> InverterState | None:
        return (self.coordinator.data or {}).get(self._address)

    @property
    def available(self) -> bool:
        """Unavailable once the inverter has stopped answering.

        Deliberately follows the library's own backoff threshold rather than
        just the coordinator's. An inverter that has gone dark must not keep
        showing the last value it managed to send — that is how a dashboard
        ends up reporting yesterday's watts at midnight.
        """
        state = self.inverter
        return super().available and state is not None and state.available
