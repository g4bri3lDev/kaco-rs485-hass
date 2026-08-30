# Changelog

## 1.0.0 (2026-08-30)


### Features

* Home Assistant integration for KACO xi inverters over RS485 ([14ec0f0](https://github.com/g4bri3lDev/kaco-rs485-hass/commit/14ec0f01212a5edb5cf572f1ba5ef8b1d4c9c310))
* install the protocol library from PyPI ([12dd0f5](https://github.com/g4bri3lDev/kaco-rs485-hass/commit/12dd0f58c2ee1f2c83c2a0c33aa04f3f1f7d94cd))
* name devices after the inverter they represent ([#4](https://github.com/g4bri3lDev/kaco-rs485-hass/issues/4)) ([e5818c3](https://github.com/g4bri3lDev/kaco-rs485-hass/commit/e5818c3344a7e8c36bda84142ccbda77a504c646))
* record the firmware version as sw_version ([#5](https://github.com/g4bri3lDev/kaco-rs485-hass/issues/5)) ([dbbeda4](https://github.com/g4bri3lDev/kaco-rs485-hass/commit/dbbeda47f21399aed3df3a1f4fdf552dc7982f2d))


### Bug fixes

* declare the library via a file:// direct reference ([1e5f54a](https://github.com/g4bri3lDev/kaco-rs485-hass/commit/1e5f54a3b71cbdad35edfa1956f3bec7d56ef338))
* drop the synthetic device for the bus ([#2](https://github.com/g4bri3lDev/kaco-rs485-hass/issues/2)) ([4722584](https://github.com/g4bri3lDev/kaco-rs485-hass/commit/47225841874b78f55402474d9bd1d356faa84b95))
* name the entry after the port, not its URL ([#3](https://github.com/g4bri3lDev/kaco-rs485-hass/issues/3)) ([a81f1c2](https://github.com/g4bri3lDev/kaco-rs485-hass/commit/a81f1c2b112b085d9581ab3143f3b95d93c35cc7))
* run the bus scan as a progress task, not inline ([61736c7](https://github.com/g4bri3lDev/kaco-rs485-hass/commit/61736c74b5424277e0130212b7ac44229e57d79a))


### Documentation

* lead the setup with the browser-installable ESPHome proxy ([adc05dd](https://github.com/g4bri3lDev/kaco-rs485-hass/commit/adc05dd6545aa8ba4e4f235301a30c2c03a3045e))
