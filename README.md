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

## Setup

1. Wire an RS485 adapter to the inverter bus. If you are using an ESPHome
   proxy, flash it with the
   [official serial-proxy config](https://github.com/esphome/serial-proxies)
   and adopt the device in Home Assistant first — this integration reaches the
   port *through* the ESPHome integration's connection.
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
