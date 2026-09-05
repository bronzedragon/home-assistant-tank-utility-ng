from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_TEMP_UNIT_MODE, CONF_CAPACITY_UNIT_MODE, CONF_REFILL_PERCENT_THRESHOLD,
    CONF_REFILL_GALLON_MIN, CONF_UPDATE_INTERVAL_HOURS, DEFAULT_TEMP_UNIT_MODE,
    DEFAULT_CAPACITY_UNIT_MODE, DEFAULT_REFILL_PERCENT_THRESHOLD,
    DEFAULT_REFILL_GALLON_MIN, DEFAULT_UPDATE_INTERVAL_HOURS, DOMAIN,
    CONF_DEVICES, GALLONS_PER_LITER,
)

_LOGGER = logging.getLogger(__name__)
STORE_KEY = f"{DOMAIN}_state"
STORE_VERSION = 1


class TankUtilityCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client):
        self.entry = entry
        self.client = client
        self.devices: list[str] = entry.data.get(CONF_DEVICES, [])
        self.store = Store(hass, STORE_VERSION, STORE_KEY)
        self.state: dict[str, Any] = {"last_gallons": {}, "total_used": {}, "_loaded": False}
        super().__init__(
            hass=hass, logger=_LOGGER, name=DOMAIN,
            update_interval=timedelta(hours=int(entry.options.get(CONF_UPDATE_INTERVAL_HOURS, DEFAULT_UPDATE_INTERVAL_HOURS))),
        )

    def _detect_temp_unit(self, temp: float | None) -> str | None:
        if temp is None:
            return None
        try:
            t = float(temp)
        except Exception:
            return None
        if t > 60:
            return "F"
        if t < -10:
            return "C"
        mode = self.entry.options.get(CONF_TEMP_UNIT_MODE, DEFAULT_TEMP_UNIT_MODE)
        if mode in ("C", "F"):
            return mode
        return "F" if self.hass.config.units.temperature_unit.endswith("F") else "C"

    def _normalize_temp_to_c(self, temp, unit):
        if temp is None or unit is None:
            return None
        t = float(temp)
        return t if unit == "C" else (t - 32.0) * 5.0 / 9.0

    def _normalize_capacity_to_gallons(self, capacity):
        if capacity is None:
            return 0.0
        cap = float(capacity)
        mode = self.entry.options.get(CONF_CAPACITY_UNIT_MODE, DEFAULT_CAPACITY_UNIT_MODE)
        if mode == "L":
            return cap * GALLONS_PER_LITER
        if mode == "gal":
            return cap
        return cap * GALLONS_PER_LITER if cap >= 600 else cap

    async def _async_update_data(self) -> dict[str, Any]:
        if not self.state.get("_loaded"):
            stored = await self.store.async_load()
            if stored:
                self.state.update(stored)
            self.state["_loaded"] = True
        try:
            if not self.devices:
                self.devices = await self.client.async_list_devices()
        except Exception as err:
            raise UpdateFailed(f"Unable to list devices: {err}") from err

        result = {}
        for dev_id in self.devices:
            try:
                js = await self.client.async_get_device(dev_id)
            except Exception as err:
                raise UpdateFailed(f"Unable to fetch device {dev_id}: {err}") from err
            device = js.get("device", js)
            last = device.get("lastReading", {})
            consumption_type = device.get("consumption_type") or {}
            consumption_types = [k for k, v in consumption_type.items() if v] if isinstance(consumption_type, dict) else []
            telemetry = device.get("telemetry") or []
            last_tlm = telemetry[0] if isinstance(telemetry, list) and telemetry else {}
            level_pct = float(last.get("tank", 0.0))
            raw_capacity = device.get("capacity")
            capacity = self._normalize_capacity_to_gallons(raw_capacity)
            cap_mode = self.entry.options.get(CONF_CAPACITY_UNIT_MODE, DEFAULT_CAPACITY_UNIT_MODE)
            capacity_unit_detected = cap_mode if cap_mode in ("L", "gal") else ("L" if float(raw_capacity or 0) >= 600 else "gal")
            gallons = capacity * level_pct / 100.0
            prev_gal = float(self.state["last_gallons"].get(dev_id, gallons))
            prev_pct = (prev_gal / capacity * 100.0) if capacity else level_pct
            delta_gal = gallons - prev_gal
            delta_pct = level_pct - prev_pct
            pct_th = float(self.entry.options.get(CONF_REFILL_PERCENT_THRESHOLD, DEFAULT_REFILL_PERCENT_THRESHOLD))
            gal_th = float(self.entry.options.get(CONF_REFILL_GALLON_MIN, DEFAULT_REFILL_GALLON_MIN))
            refill = (delta_pct >= pct_th) or (delta_gal >= gal_th)
            consumed = 0.0 if refill else max(prev_gal - gallons, 0.0)
            total_used = float(self.state["total_used"].get(dev_id, 0.0))
            if not refill:
                total_used += consumed
            self.state["last_gallons"][dev_id] = gallons
            self.state["total_used"][dev_id] = total_used
            temp_raw = last.get("temperature")
            temp_unit = self._detect_temp_unit(temp_raw)
            temp_c = self._normalize_temp_to_c(temp_raw, temp_unit)
            result[dev_id] = {
                "device_id": dev_id,
                "name": device.get("short_device_id") or device.get("name") or dev_id,
                "short_device_id": device.get("short_device_id"),
                "fuel_type": device.get("fuel_type"),
                "product_name": device.get("product_name") or device.get("product_id"),
                "capacity_gal": round(capacity, 3), "capacity_unit_detected": capacity_unit_detected,
                "level_pct": round(level_pct, 3), "gallons_remaining": round(gallons, 3),
                "temperature_c": None if temp_c is None else round(float(temp_c), 3),
                "temperature_unit": temp_unit, "temperature_raw": temp_raw,
                "average_consumption": device.get("average_consumption"),
                "avg_consumption_gpd": device.get("average_consumption"),
                "estimated_fill_date": device.get("estimated_fill_date"), "last_updated": last.get("time_iso"),
                "refill_detected": refill, "delta_gal": round(delta_gal, 3),
                "consumed_gal": round(consumed, 3), "total_used_gal": round(total_used, 3),
                "battery_warn": bool(device.get("battery_warn")), "battery_crit": bool(device.get("battery_crit")),
                "battery_level": device.get("battery_level"), "orientation": device.get("orientation"),
                "consumption_types": consumption_types, "telemetry_rssi": last_tlm.get("rssi"),
                "telemetry_ssid": last_tlm.get("ssid"), "telemetry_http_status": last_tlm.get("http_status_code"),
                "telemetry_time": last_tlm.get("tlm_time"), "telemetry_type": last_tlm.get("type"),
                "telemetry_time_to_conn": last_tlm.get("time_to_conn"),
            }
        await self.store.async_save({"last_gallons": self.state["last_gallons"], "total_used": self.state["total_used"]})
        return result
