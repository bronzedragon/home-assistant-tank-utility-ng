from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

FRONTEND_URL = "/tank_utility_ng/frontend"
CARD_URL = f"{FRONTEND_URL}/tank-utility-ng-gauge.js"
FRONTEND_DIR = Path(__file__).parent / "frontend"


async def async_register_frontend(hass: HomeAssistant) -> None:
    """Serve and register the bundled Tank Utility NG Lovelace card."""
    await hass.http.async_register_static_paths(
        [StaticPathConfig(FRONTEND_URL, str(FRONTEND_DIR), False)]
    )

    lovelace_data = hass.data.get("lovelace")
    if lovelace_data is None:
        _LOGGER.debug("Lovelace is not loaded; bundled gauge resource was not auto-registered")
        return

    resources = getattr(lovelace_data, "resources", None)
    if resources is None:
        _LOGGER.debug("Lovelace resources are YAML-managed; add %s manually as a module", CARD_URL)
        return

    if not resources.loaded:
        await resources.async_load()

    if any(item.get("url", "").split("?", 1)[0] == CARD_URL for item in resources.async_items()):
        return

    await resources.async_create_item({"res_type": "module", "url": CARD_URL})
    _LOGGER.info("Registered bundled Tank Utility NG Gauge Lovelace resource")
