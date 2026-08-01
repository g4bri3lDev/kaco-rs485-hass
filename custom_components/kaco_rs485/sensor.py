"""Sensors.

Two commands feed these: `0` for the fast-changing electrical values and `3`
for the yield and hour counters. An inverter that has answered one but not the
other reports `None` for the missing half rather than a stale value.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from kaco_rs485 import InverterState, status_text
from kaco_rs485.status import is_fault

from .coordinator import KacoRs485ConfigEntry, KacoRs485Coordinator
from .entity import KacoRs485Entity


def _hours(value: str | None) -> float | None:
    """`hhhhhh:mm` -> hours. Six-digit hour counts overflow any time type."""
    if not value or ":" not in value:
        return None
    hours, _, minutes = value.partition(":")
    try:
        return int(hours) + int(minutes) / 60
    except ValueError:
        return None


@dataclass(frozen=True, kw_only=True)
class KacoSensorDescription(SensorEntityDescription):
    """A sensor plus how to pull its value out of an InverterState."""

    value_fn: Callable[[InverterState], float | str | None]


SENSORS: tuple[KacoSensorDescription, ...] = (
    # --- command `0`: measured values ---
    KacoSensorDescription(
        key="ac_power",
        translation_key="ac_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.measured.ac_power_w if s.measured else None,
    ),
    KacoSensorDescription(
        key="ac_voltage",
        translation_key="ac_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda s: s.measured.ac_voltage_v if s.measured else None,
    ),
    KacoSensorDescription(
        key="ac_current",
        translation_key="ac_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda s: s.measured.ac_current_a if s.measured else None,
    ),
    KacoSensorDescription(
        key="dc_power",
        translation_key="dc_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.measured.dc_power_w if s.measured else None,
    ),
    KacoSensorDescription(
        key="dc_voltage",
        translation_key="dc_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda s: s.measured.dc_voltage_v if s.measured else None,
    ),
    KacoSensorDescription(
        key="dc_current",
        translation_key="dc_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda s: s.measured.dc_current_a if s.measured else None,
    ),
    KacoSensorDescription(
        key="efficiency",
        translation_key="efficiency",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_registry_enabled_default=False,
        # Only meaningful while actually converting; at low DC power the
        # quotient is dominated by the inverter's own consumption and swings
        # wildly, so it is suppressed rather than reported as nonsense.
        value_fn=lambda s: (
            round(100 * s.measured.ac_power_w / s.measured.dc_power_w, 1)
            if s.measured and s.measured.dc_power_w > 100
            else None
        ),
    ),
    KacoSensorDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.measured.temperature_c if s.measured else None,
    ),
    KacoSensorDescription(
        key="daily_yield",
        translation_key="daily_yield",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda s: s.measured.daily_yield_wh if s.measured else None,
    ),
    # --- command `3`: counters ---
    KacoSensorDescription(
        key="total_yield",
        translation_key="total_yield",
        device_class=SensorDeviceClass.ENERGY,
        # kWh on xi units. The same field is Wh on blueplanet hardware, which
        # this integration does not talk to — those units answer with the
        # CRC16 Generic Protocol and are rejected during discovery.
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda s: s.totals.total_yield_raw if s.totals else None,
    ),
    KacoSensorDescription(
        key="daily_peak_power",
        translation_key="daily_peak_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.totals.daily_peak_w if s.totals else None,
    ),
    KacoSensorDescription(
        key="total_uptime",
        translation_key="total_uptime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=0,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: _hours(s.totals.total_uptime if s.totals else None),
    ),
    KacoSensorDescription(
        key="daily_uptime",
        translation_key="daily_uptime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda s: _hours(s.totals.daily_uptime if s.totals else None),
    ),
    # --- status ---
    KacoSensorDescription(
        key="status",
        translation_key="status",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: status_text(s.measured.status) if s.measured else None,
    ),
    KacoSensorDescription(
        key="status_code",
        translation_key="status_code",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        # The raw number is what the manual is indexed by, so it stays
        # available even though the text is the friendlier reading.
        value_fn=lambda s: s.measured.status if s.measured else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KacoRs485ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        KacoRs485Sensor(coordinator, address, description)
        for address in coordinator.data
        for description in SENSORS
    )


class KacoRs485Sensor(KacoRs485Entity, SensorEntity):
    entity_description: KacoSensorDescription

    def __init__(
        self,
        coordinator: KacoRs485Coordinator,
        address: int,
        description: KacoSensorDescription,
    ) -> None:
        super().__init__(coordinator, address)
        self.entity_description = description
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{address}_{description.key}"
        )

    @property
    def native_value(self) -> float | str | None:
        state = self.inverter
        return self.entity_description.value_fn(state) if state else None

    @property
    def extra_state_attributes(self) -> dict[str, bool] | None:
        """Flag fault states on the status sensor.

        The code table splits into operating states and fault states, and the
        distinction is the actionable part — an automation wants to fire on
        "this inverter has tripped", not on every status change.
        """
        if self.entity_description.key != "status":
            return None
        state = self.inverter
        if state is None or state.measured is None:
            return None
        return {"is_fault": is_fault(state.measured.status)}
