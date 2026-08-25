"""Config flow.

The port is chosen with `SerialPortSelector`, which lists local serial devices
*and* ESPHome serial proxies and hands back a URL string. That is why this
integration stores no host, no port number and no API key: for a proxied port
the URL is `esphome-hass://esphome/<entry_id>?port_name=...`, and Home
Assistant resolves it against the ESPHome integration's own authenticated
connection.

Addresses are discovered by scanning rather than asked for. They are set on
each inverter's front panel and nothing announces them, so the only
alternatives are asking a human to remember or asking the bus. Scanning is slow
— every silent address costs a full reply timeout — but it happens once and it
cannot be misremembered.
"""

from __future__ import annotations

import asyncio
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PORT
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    SerialPortSelector,
)

from kaco_rs485 import AsyncBus, BusError
from kaco_rs485.discovery import ALL_ADDRESSES, ScanResult, scan

from .const import CONF_ADDRESSES, DOMAIN, LOGGER


class KacoRs485ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Pick a port, scan it, confirm what was found."""

    VERSION = 1

    def __init__(self) -> None:
        self._port: str | None = None
        self._result: ScanResult | None = None
        self._scan_task: asyncio.Task[ScanResult] | None = None
        self._scan_error: str | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if self._scan_error:
            errors["base"] = self._scan_error
            self._scan_error = None

        if user_input is not None:
            self._port = user_input[CONF_PORT]
            await self.async_set_unique_id(self._port)
            self._abort_if_unique_id_configured()
            return await self.async_step_scan()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_PORT): SerialPortSelector()}),
            errors=errors,
        )

    async def async_step_scan(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Run the bus scan as a background task, showing progress.

        This cannot be done inline. Probing 32 addresses costs a reply timeout
        for every one that is empty, so a sparse bus takes tens of seconds and
        a slow one considerably longer. A config-flow step that blocks for that
        long just renders as a spinner that never resolves.
        """
        assert self._port is not None

        if self._scan_task is None:
            self._scan_task = self.hass.async_create_task(self._scan(self._port))

        if not self._scan_task.done():
            return self.async_show_progress(
                step_id="scan",
                progress_action="scanning",
                progress_task=self._scan_task,
            )

        try:
            self._result = self._scan_task.result()
        except BusError:
            LOGGER.exception("Scanning %s failed", self._port)
            self._scan_error = "cannot_connect"
            return self.async_show_progress_done(next_step_id="user")
        finally:
            self._scan_task = None

        return self.async_show_progress_done(next_step_id="confirm")

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show what the scan found and let the user adjust it."""
        assert self._port is not None
        assert self._result is not None

        found = [d.address for d in self._result.supported]

        if not found:
            # An empty scan is genuinely ambiguous: these inverters stop
            # answering entirely at night, so this may be a wiring fault or
            # may just be dark. Do not create an entry with nothing in it, and
            # do not claim to know which case it is.
            return self.async_abort(
                reason="no_inverters",
                description_placeholders={
                    "detail": (
                        "Nothing answered. KACO inverters stop responding "
                        "entirely when the sun is down, so try again in "
                        "daylight before suspecting the wiring."
                    )
                },
            )

        if user_input is not None:
            return self.async_create_entry(
                title=self._port,
                data={
                    CONF_PORT: self._port,
                    # The selector hands back strings; the library wants ints.
                    CONF_ADDRESSES: [int(a) for a in user_input[CONF_ADDRESSES]],
                },
            )

        described = ", ".join(
            f"{d.address} ({d.inverter_type or 'unknown type'})" for d in self._result.supported
        )
        unsupported = ", ".join(str(d.address) for d in self._result.unsupported)

        options = [
            SelectOptionDict(
                value=str(d.address),
                label=f"{d.address} — {d.inverter_type or 'unknown type'}",
            )
            for d in self._result.supported
        ]

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESSES, default=[str(a) for a in found]): SelectSelector(
                        SelectSelectorConfig(
                            options=options,
                            multiple=True,
                            mode=SelectSelectorMode.LIST,
                        )
                    )
                }
            ),
            description_placeholders={
                "found": described,
                # Named, not silently dropped: a blueplanet on the bus is a
                # real device that this integration cannot read, and leaving
                # it unexplained sends people hunting a fault.
                "unsupported": (
                    f"Address(es) {unsupported} answered with the CRC16 Generic "
                    "Protocol. Those are blueplanet or TL/TR units, which are "
                    "read over Modbus TCP instead and are ignored here."
                    if unsupported
                    else ""
                ),
            },
        )

    async def _scan(self, port: str) -> ScanResult:
        """Probe the whole bus. Slow, but it only happens once."""
        LOGGER.debug("Scanning %s for KACO inverters", port)
        async with AsyncBus(port) as bus:
            return await scan(bus, ALL_ADDRESSES)
