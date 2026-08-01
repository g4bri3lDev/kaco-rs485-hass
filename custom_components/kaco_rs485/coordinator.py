"""Polling coordinator.

The bus is a shared medium and the library paces itself between individual
requests, so this coordinator's only jobs are to own the connection, run one
cycle per interval, and reopen the port when it goes away.
"""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from kaco_rs485 import AsyncBus, BusError, InverterState, KacoRs485Client

from .const import DOMAIN, LOGGER, SCAN_INTERVAL_SECONDS

type KacoRs485ConfigEntry = ConfigEntry[KacoRs485Coordinator]


class KacoRs485Coordinator(DataUpdateCoordinator[dict[int, InverterState]]):
    """Runs one poll cycle per interval over a single long-lived connection."""

    config_entry: KacoRs485ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: KacoRs485ConfigEntry,
        port: str,
        addresses: list[int],
    ) -> None:
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self._bus = AsyncBus(port)
        self._client = KacoRs485Client(self._bus, addresses)
        self._opened = False

    async def async_open(self) -> None:
        await self._bus.open()
        self._opened = True

    async def async_close(self) -> None:
        if self._opened:
            await self._bus.close()
            self._opened = False

    async def _async_update_data(self) -> dict[int, InverterState]:
        # The proxy can go away and take the port with it — a firmware update,
        # a reboot, a wifi drop. Reopen rather than failing every cycle from
        # here on.
        if not self._opened:
            try:
                await self.async_open()
            except BusError as err:
                raise UpdateFailed(f"Cannot open the RS485 port: {err}") from err

        try:
            return await self._client.poll_cycle()
        except BusError as err:
            # Drop the connection so the next cycle reopens it.
            await self.async_close()
            raise UpdateFailed(f"RS485 bus error: {err}") from err
