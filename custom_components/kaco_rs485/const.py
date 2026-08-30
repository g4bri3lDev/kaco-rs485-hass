"""Constants for the KACO RS485 integration."""

from __future__ import annotations

import logging
from typing import Final

DOMAIN: Final = "kaco_rs485"
LOGGER: Final = logging.getLogger(__package__)

CONF_ADDRESSES: Final = "addresses"

# `{"1": {"model": "6400xi", "sw_version": "K222.36DE 6817"}, ...}` — what each
# address reported during the setup scan, keyed by address as a string because
# entry data is JSON.
#
# Stored rather than read from the current poll because these inverters stop
# answering entirely once the sun is down, so a restart at night would build
# every device with nothing on it. The scan captures both while the inverter is
# demonstrably awake, and the flow refuses to create an entry when nothing
# answered.
CONF_INVERTERS: Final = "inverters"
CONF_MODEL: Final = "model"
CONF_SW_VERSION: Final = "sw_version"

# The KACO standard protocol allows RS485 addresses 1-32. Which ones are in
# use is discovered by scanning; it is never assumed.
MIN_ADDRESS: Final = 1
MAX_ADDRESS: Final = 32

# One full round of the bus. The library paces itself between individual
# requests, so this is the gap between cycles, not between inverters.
SCAN_INTERVAL_SECONDS: Final = 30

MANUFACTURER: Final = "KACO new energy"

# Inverters report a bare type string ("6400xi"); the series name is not on the
# bus. Hardcoded because this integration is xi-only, and the xi range is all
# Powador — blueplanet and TL/TR units are named as unsupported during setup.
SERIES_PREFIX: Final = "KACO Powador"
