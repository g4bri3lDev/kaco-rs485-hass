# KACO RS485 for Home Assistant

Reads KACO Powador **xi-series** inverters (6400xi, 8000xi and relatives) over
RS485 — from a serial adapter on the Home Assistant host, or across the network
through an [ESPHome serial proxy](https://esphome.io/components/serial_proxy/).

Protocol handling lives in [`kaco-rs485`](https://github.com/g4bri3lDev/kaco-rs485).
Companion to [`kaco-modbus-hass`](https://github.com/g4bri3lDev/kaco-modbus-hass),
which covers newer blueplanet units over SunSpec Modbus TCP — the two use
different domains and coexist happily.

## Requirements

Home Assistant **2026.5** or newer, for the serial-port selector and the
ESPHome serial proxy support.

The protocol library, [`kaco-serial`](https://pypi.org/project/kaco-serial/),
is declared in `manifest.json` and installed by Home Assistant itself — there
is nothing to install by hand.

To develop against a local checkout of the library instead, point the
requirement at it:

```json
"requirements": ["kaco-serial @ file:///path/to/kaco-rs485"]
```

## Setup

1. Get an RS485 port onto the network, or plug an adapter into the machine
   running Home Assistant.

   The least work is the ready-made ESPHome project for the **M5Stack AtomS3
   Lite with an ATOMIC RS485 Base**: it installs
   [from the browser](https://esphome.io/projects/?type=serial), no YAML and no
   toolchain. For other hardware, the
   [serial-proxies repository](https://github.com/esphome/serial-proxies) has
   tested configurations, and the
   [`serial_proxy` component](https://esphome.io/components/serial_proxy/)
   documents the rest.

   Adopt the device in Home Assistant **before** adding this integration: the
   port is reached *through* the ESPHome integration's connection, so it has to
   exist first.

   A proxy is also the only way to reach a bus that is not physically next to
   Home Assistant, and it keeps the link encrypted and authenticated rather
   than exposing a raw socket.
2. Add the integration and pick the port. Local devices and ESPHome proxies
   appear in the same list.
3. It scans all 32 addresses and shows what answered. Confirm which to monitor.

**Inverters can only be added while the sun is up.** These units shut down
completely at dusk — not into a standby that still answers, but off the bus
entirely — so a night-time scan finds nothing at all. Setup refuses to create
an empty entry, because an empty scan cannot tell you whether the wiring is
wrong or it is simply dark.

Measured on a three-inverter bus (2026-08-30, sunset 19:58 local): the units
dropped to 0 W around 19:15 and spent the next hour cycling between *Waiting*,
*Constant voltage mode* and *MPP tracking* while still answering normally, then
went silent between **20:13 and 20:19** — fifteen to twenty minutes after
sunset. One reported *Waiting for shutdown* as its last status. They answer
nothing at all until morning.

This is also why each inverter's model is recorded during setup rather than
read from the current poll: a Home Assistant restart at night would otherwise
leave every device unnamed until sunrise.

**Only one device may poll an RS485 bus.** If a datalogger is still connected,
disconnect it — two masters corrupt each other's traffic.

## Entities

One device per inverter, named for what it reported during setup — e.g.
**KACO Powador 6400xi (1)**, where the number is the RS485 address set on that
inverter's own front panel. The address is always part of the name: two
identical units on one bus is the ordinary case, and xi inverters expose no
serial number to tell them apart (the protocol's serial command is answered
only by blueplanet hardware). Rename the devices in Home Assistant if you would
rather they were "Garage roof".

Enabled by default:

| entity | notes |
|---|---|
| AC power, DC power | instantaneous |
| Temperature | inverter internal |
| Daily yield | Wh, resets daily |
| Total yield | kWh, feeds the energy dashboard |
| Daily peak power | highest AC power today |
| Total operating hours | diagnostic |
| Status | text, with an `is_fault` attribute |

Disabled by default, enable if you want them: AC/DC voltage and current,
efficiency, daily operating hours, and the raw status code.

The status text covers all 119 documented KACO codes. Labels are normalised —
where the vendor's English and German tables disagree, the German is used,
because the English table has over/under inverted for several grid-voltage
faults.

### Unavailability

An inverter that stops answering is reported `unavailable` rather than holding
its last value. This is deliberate: every one of these units goes dark
overnight, and a dashboard that keeps showing the evening's watts at 2 a.m. is
worse than one that admits it does not know.

## Energy dashboard

Add each inverter's **Total yield** as a solar production source. It is a
`total_increasing` kWh counter read from the inverter's own lifetime register,
so it survives Home Assistant restarts and does not need a Riemann sum.

## Limitations

- **xi-series only.** blueplanet, TL and TR units answer the same request with
  a different protocol (CRC16 Generic). They are detected during setup and
  named as unsupported rather than silently skipped — use `kaco-modbus-hass`
  for those.
- **Read-only.** The hardware also accepts active and reactive power limiting
  commands. Those are not implemented.
- Polling is paced deliberately (one request per second per inverter, in
  sequence). A bus of three inverters takes a few seconds per cycle; this is a
  property of RS485, not a bug.
