from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfTemperature, UnitOfVolume
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify
from .const import DOMAIN, PROPANE_KWH_PER_GALLON, GAL_PROPANE_TO_FT3

@dataclass(frozen=True)
class Desc:
    key: str
    name: str
    unit: str | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None
    entity_category: EntityCategory | None = None
    icon: str | None = None

SENSORS = [
    Desc("level_pct", "Tank Level", PERCENTAGE, None, SensorStateClass.MEASUREMENT, None, "mdi:propane-tank"),
    Desc("gallons_remaining", "Gallons Remaining", UnitOfVolume.GALLONS, None, SensorStateClass.MEASUREMENT, None, "mdi:propane-tank-outline"),
    Desc("temperature_c", "Tank Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, None, "mdi:thermometer"),
    Desc("avg_consumption_gpd", "Average Consumption", "gal/day", None, SensorStateClass.MEASUREMENT, None, "mdi:chart-line"),
    Desc("estimated_fill_date", "Estimated Refill Date", None, SensorDeviceClass.TIMESTAMP, None, None, "mdi:calendar-clock"),
]
DIAG_SENSORS = [
    Desc("last_updated", "Last Reading", None, SensorDeviceClass.TIMESTAMP, None, EntityCategory.DIAGNOSTIC, "mdi:clock-outline"),
    Desc("capacity_gal", "Tank Capacity", UnitOfVolume.GALLONS, None, SensorStateClass.MEASUREMENT, EntityCategory.DIAGNOSTIC, "mdi:propane-tank"),
    Desc("orientation", "Tank Orientation", None, None, None, EntityCategory.DIAGNOSTIC, "mdi:rotate-orbit"),
    Desc("battery_level", "Battery Level", None, None, None, EntityCategory.DIAGNOSTIC, "mdi:battery"),
    Desc("telemetry_rssi", "Signal Strength", "dBm", SensorDeviceClass.SIGNAL_STRENGTH, SensorStateClass.MEASUREMENT, EntityCategory.DIAGNOSTIC, "mdi:wifi-strength-2"),
    Desc("telemetry_http_status", "Last Upload HTTP Status", None, None, None, EntityCategory.DIAGNOSTIC, "mdi:http"),
    Desc("telemetry_ssid", "Wi-Fi SSID", None, None, None, EntityCategory.DIAGNOSTIC, "mdi:wifi"),
]

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []
    for dev_id in coordinator.data.keys():
        for desc in SENSORS:
            entities.append(TankUtilitySensor(coordinator, dev_id, desc))
        entities.extend([PropaneConsumedGallonsTotal(coordinator, dev_id), GasConsumedFt3Total(coordinator, dev_id), EnergyConsumedKwhTotal(coordinator, dev_id), PropaneEnergyRemainingKwh(coordinator, dev_id)])
        for desc in DIAG_SENSORS:
            entities.append(TankUtilitySensor(coordinator, dev_id, desc))
        entities.append(TelemetryLastSeen(coordinator, dev_id))
    async_add_entities(entities, update_before_add=True)
    hass.async_create_task(coordinator.async_request_refresh())

class _Base(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    def __init__(self, coordinator, dev_id: str):
        super().__init__(coordinator)
        self.dev_id = dev_id
    @property
    def device_info(self) -> DeviceInfo:
        data = self.coordinator.data[self.dev_id]
        return DeviceInfo(identifiers={(DOMAIN, self.dev_id)}, name=data.get("short_device_id") or data.get("name") or self.dev_id, manufacturer="Tank Utility", model=(data.get("product_name") or "Tank Monitor") + (f" ({data.get('fuel_type')})" if data.get("fuel_type") else ""))

class TankUtilitySensor(_Base):
    def __init__(self, coordinator, dev_id: str, desc: Desc):
        super().__init__(coordinator, dev_id)
        self.desc = desc
        short_id = coordinator.data[dev_id].get("short_device_id") or dev_id
        self._attr_unique_id = f"{short_id}_{desc.key}"
        self._attr_name = desc.name
        self._attr_suggested_object_id = slugify(f"{short_id}_{desc.key}")
        self._attr_native_unit_of_measurement = desc.unit
        self._attr_device_class = desc.device_class
        self._attr_state_class = desc.state_class
        self._attr_entity_category = desc.entity_category
        self._attr_icon = desc.icon
    @property
    def native_value(self):
        value = self.coordinator.data[self.dev_id].get(self.desc.key)
        if self._attr_device_class == SensorDeviceClass.TIMESTAMP and isinstance(value, str):
            dt = dt_util.parse_datetime(value)
            if dt is None: return None
            return dt_util.as_utc(dt) if dt.tzinfo else dt_util.as_utc(dt.replace(tzinfo=timezone.utc))
        return value
    @property
    def extra_state_attributes(self):
        data = self.coordinator.data.get(self.dev_id, {})
        attrs = {"device_id": data.get("device_id") or self.dev_id, "short_device_id": data.get("short_device_id")}
        if self.desc.key in ("level_pct", "capacity_gal"):
            attrs.update({"fuel_type": data.get("fuel_type"), "orientation": data.get("orientation"), "consumption_types": data.get("consumption_types"), "capacity_unit_detected": data.get("capacity_unit_detected")})
        if self.desc.key == "temperature_c": attrs.update({"reported_temperature": data.get("temperature_raw"), "reported_unit_detected": data.get("temperature_unit")})
        if self.desc.key == "telemetry_rssi": attrs.update({"ssid": data.get("telemetry_ssid"), "http_status_code": data.get("telemetry_http_status"), "type": data.get("telemetry_type"), "time_to_conn": data.get("telemetry_time_to_conn")})
        return attrs

class PropaneConsumedGallonsTotal(_Base):
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfVolume.GALLONS
    def __init__(self, coordinator, dev_id: str):
        super().__init__(coordinator, dev_id); short_id = coordinator.data[dev_id].get("short_device_id") or dev_id
        self._attr_unique_id=f"{short_id}_propane_consumed_gal_total"; self._attr_name="Propane Consumption"; self._attr_icon="mdi:fire"; self._attr_suggested_object_id=slugify(f"{short_id}_propane_consumed_gal_total")
    @property
    def native_value(self): return self.coordinator.data[self.dev_id].get("total_used_gal")

class GasConsumedFt3Total(_Base):
    _attr_device_class=SensorDeviceClass.GAS; _attr_state_class=SensorStateClass.TOTAL_INCREASING; _attr_native_unit_of_measurement=UnitOfVolume.CUBIC_FEET
    def __init__(self, coordinator, dev_id: str):
        super().__init__(coordinator, dev_id); short_id=coordinator.data[dev_id].get("short_device_id") or dev_id
        self._attr_unique_id=f"{short_id}_gas_consumed_ft3_total"; self._attr_name="Gas Consumption"; self._attr_icon="mdi:gas-cylinder"; self._attr_suggested_object_id=slugify(f"{short_id}_gas_consumed_ft3_total")
    @property
    def native_value(self): return round(float(self.coordinator.data[self.dev_id].get("total_used_gal") or 0.0)*GAL_PROPANE_TO_FT3,3)

class EnergyConsumedKwhTotal(_Base):
    _attr_device_class=SensorDeviceClass.ENERGY; _attr_state_class=SensorStateClass.TOTAL_INCREASING; _attr_native_unit_of_measurement="kWh"
    def __init__(self, coordinator, dev_id: str):
        super().__init__(coordinator, dev_id); short_id=coordinator.data[dev_id].get("short_device_id") or dev_id
        self._attr_unique_id=f"{short_id}_energy_consumed_kwh_total"; self._attr_name="Energy Consumption"; self._attr_icon="mdi:lightning-bolt"; self._attr_suggested_object_id=slugify(f"{short_id}_energy_consumed_kwh_total")
    @property
    def native_value(self): return round(float(self.coordinator.data[self.dev_id].get("total_used_gal") or 0.0)*PROPANE_KWH_PER_GALLON,3)

class PropaneEnergyRemainingKwh(_Base):
    _attr_device_class=SensorDeviceClass.ENERGY; _attr_state_class=None; _attr_native_unit_of_measurement="kWh"
    def __init__(self, coordinator, dev_id: str):
        super().__init__(coordinator, dev_id); short_id=coordinator.data[dev_id].get("short_device_id") or dev_id
        self._attr_unique_id=f"{short_id}_energy_remaining_kwh"; self._attr_name="Energy Remaining"; self._attr_icon="mdi:lightning-bolt-outline"; self._attr_suggested_object_id=slugify(f"{short_id}_energy_remaining_kwh")
    @property
    def native_value(self): return round(float(self.coordinator.data[self.dev_id].get("gallons_remaining") or 0.0)*PROPANE_KWH_PER_GALLON,3)

class TelemetryLastSeen(_Base):
    _attr_device_class=SensorDeviceClass.TIMESTAMP; _attr_entity_category=EntityCategory.DIAGNOSTIC
    def __init__(self, coordinator, dev_id: str):
        super().__init__(coordinator, dev_id); short_id=coordinator.data[dev_id].get("short_device_id") or dev_id
        self._attr_unique_id=f"{short_id}_telemetry_last_seen"; self._attr_name="Telemetry Last Seen"; self._attr_icon="mdi:clock-check-outline"; self._attr_suggested_object_id=slugify(f"{short_id}_telemetry_last_seen")
    @property
    def native_value(self):
        tlm_time=self.coordinator.data[self.dev_id].get("telemetry_time")
        if tlm_time is None: return None
        try: return datetime.fromtimestamp(float(tlm_time),tz=timezone.utc)
        except Exception: return None
