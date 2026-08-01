"""Constants for the KACO RS485 integration."""

from __future__ import annotations

import logging
from typing import Final

DOMAIN: Final = "kaco_rs485"
LOGGER: Final = logging.getLogger(__package__)

CONF_ADDRESSES: Final = "addresses"

# The KACO standard protocol allows RS485 addresses 1-32. Which ones are in
# use is discovered by scanning; it is never assumed.
MIN_ADDRESS: Final = 1
MAX_ADDRESS: Final = 32

# One full round of the bus. The library paces itself between individual
# requests, so this is the gap between cycles, not between inverters.
SCAN_INTERVAL_SECONDS: Final = 30

MANUFACTURER: Final = "KACO new energy"
