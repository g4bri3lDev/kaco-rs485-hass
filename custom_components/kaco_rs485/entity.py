"""Shared entity base.

One Home Assistant device per inverter, all of them children of the serial
port they share. That mirrors the physical arrangement — several inverters on
one RS485 bus — and means a port that goes away degrades one place rather than
appearing as several unrelated failures.
"""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from kaco_rs485 import InverterState

from .const import DOMAIN, MANUFACTURER
from .coordinator import KacoRs485Coordinator


class KacoRs485Entity(CoordinatorEntity[KacoRs485Coordinator]):
    """Base for every entity belonging to one inverter."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: KacoRs485Coordinator, address: int) -> None:
        super().__init__(coordinator)
        self._address = address

        entry_id = coordinator.config_entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry_id}_{address}")},
            name=f"Inverter {address}",
            manufacturer=MANUFACTURER,
            model=self._model(),
            via_device=(DOMAIN, entry_id),
        )

    def _model(self) -> str | None:
        """The type string the inverter reports, e.g. "6400xi"."""
        state = self.inverter
        return state.measured.inverter_type if state and state.measured else None

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
