from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for dev_id in coordinator.data.keys():
        entities.append(DeliveryDetected(coordinator, dev_id))
        entities.append(BatteryWarning(coordinator, dev_id))
        entities.append(BatteryCritical(coordinator, dev_id))
    async_add_entities(entities, update_before_add=True)


class _Base(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, dev_id: str):
        super().__init__(coordinator)
        self.dev_id = dev_id

    @property
    def device_info(self) -> DeviceInfo:
        data = self.coordinator.data[self.dev_id]
        return DeviceInfo(
            identifiers={(DOMAIN, self.dev_id)},
            name=data.get("short_device_id") or data.get("name") or self.dev_id,
            manufacturer="Tank Utility",
            model=(data.get("product_name") or "Tank Monitor") + (f" ({data.get('fuel_type')})" if data.get("fuel_type") else ""),
        )


class DeliveryDetected(_Base):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator, dev_id: str):
        super().__init__(coordinator, dev_id)
        short_id = coordinator.data[dev_id].get("short_device_id") or dev_id
        self._attr_unique_id = f"{short_id}_delivery_detected"
        self._attr_name = "Delivery Detected"
        self._attr_icon = "mdi:truck-delivery"
        self._attr_suggested_object_id = slugify(f"{short_id}_delivery_detected")

    @property
    def is_on(self):
        return bool(self.coordinator.data[self.dev_id].get("refill_detected"))


class BatteryWarning(_Base):
    _attr_device_class = BinarySensorDeviceClass.BATTERY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, dev_id: str):
        super().__init__(coordinator, dev_id)
        short_id = coordinator.data[dev_id].get("short_device_id") or dev_id
        self._attr_unique_id = f"{short_id}_battery_warn"
        self._attr_name = "Battery Warning"
        self._attr_icon = "mdi:battery-alert"
        self._attr_suggested_object_id = slugify(f"{short_id}_battery_warn")

    @property
    def is_on(self):
        return bool(self.coordinator.data[self.dev_id].get("battery_warn"))


class BatteryCritical(_Base):
    _attr_device_class = BinarySensorDeviceClass.BATTERY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, dev_id: str):
        super().__init__(coordinator, dev_id)
        short_id = coordinator.data[dev_id].get("short_device_id") or dev_id
        self._attr_unique_id = f"{short_id}_battery_crit"
        self._attr_name = "Battery Critical"
        self._attr_icon = "mdi:battery-alert-variant"
        self._attr_suggested_object_id = slugify(f"{short_id}_battery_crit")

    @property
    def is_on(self):
        return bool(self.coordinator.data[self.dev_id].get("battery_crit"))
