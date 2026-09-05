from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import slugify
from homeassistant.helpers.typing import ConfigType
from .const import DOMAIN, LEGACY_DOMAIN
from .frontend import async_register_frontend


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    await async_register_frontend(hass)
    legacy = config.get(LEGACY_DOMAIN)
    if isinstance(legacy, list):
        for conf in legacy:
            hass.async_create_task(hass.config_entries.flow.async_init(DOMAIN, context={"source": "import"}, data=conf))
    return True


async def async_update_options(hass: HomeAssistant, entry):
    await hass.config_entries.async_reload(entry.entry_id)


async def async_create_entity_id_migration_issue(hass: HomeAssistant, entry) -> None:
    reg = er.async_get(hass)
    entries = er.async_entries_for_config_entry(reg, entry.entry_id)
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not coordinator or not getattr(coordinator, "data", None): return
    first = next(iter(coordinator.data.values()), {})
    short_id = first.get("short_device_id")
    if not short_id: return
    prefix = f"sensor.{slugify(short_id)}_"
    mismatch = any(e.domain == "sensor" and not e.entity_id.startswith(prefix) for e in entries)
    if not mismatch:
        ir.async_delete_issue(hass, DOMAIN, "entity_id_migration")
        return
    ir.async_create_issue(hass, DOMAIN, "entity_id_migration", is_fixable=False, severity=ir.IssueSeverity.WARNING, translation_key="entity_id_migration", translation_placeholders={"short_id": short_id, "example": f"sensor.{slugify(short_id)}_tank_level"})


async def async_setup_entry(hass: HomeAssistant, entry):
    from .api import TankUtilityClient
    from .coordinator import TankUtilityCoordinator
    client = TankUtilityClient(hass, entry.data)
    coordinator = TankUtilityCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])
    return True


async def async_unload_entry(hass: HomeAssistant, entry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "binary_sensor"])
    if unload_ok: hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
