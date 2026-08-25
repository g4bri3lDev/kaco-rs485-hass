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

**Do the setup scan in daylight.** These inverters stop answering entirely when
the sun is down, so a night-time scan finds nothing and cannot tell you whether
that is a wiring problem or just darkness.

**Only one device may poll an RS485 bus.** If a datalogger is still connected,
disconnect it — two masters corrupt each other's traffic.

## Entities

One device per inverter. Enabled by default:

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
