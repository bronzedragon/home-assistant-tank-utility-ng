# Tank Utility NG

A modern Home Assistant custom integration for Tank Utility propane tank monitors.

## Features
- UI config and options flows
- Tank level, temperature, capacity, orientation, average consumption, and estimated refill date
- Gallons remaining and propane kWh equivalence
- Energy Dashboard-compatible cumulative gas and energy sensors
- Delivery detection and delivery-volume estimation groundwork
- Battery and Wi-Fi telemetry diagnostics
- Automatic temperature and volume-unit handling
- Conservative configurable polling for Tank Utility API rate limits
- Entity-ID migration guidance
- **Included `tank-utility-ng-gauge` Lovelace card** with capacity/orientation-aware tank artwork, static fill level, gauge colors, and delivery highlighting
- HACS-compatible repository layout

## HACS
Add this repository to HACS as an **Integration**, install **Tank Utility NG**, restart Home Assistant, then add it from **Settings → Devices & services**.

The integration serves and registers its bundled Lovelace card automatically when Lovelace resources are storage-managed. If your Lovelace resources are YAML-managed, add `/tank_utility_ng/frontend/tank-utility-ng-gauge.js` as a JavaScript module manually.

## Included Lovelace card

```yaml
type: custom:tank-utility-ng-gauge
tank_level: sensor.house_tank_tank_level
gallons_remaining: sensor.house_tank_gallons_remaining
tank_capacity: sensor.house_tank_tank_capacity
delivery: binary_sensor.house_tank_delivery_detected
```

`orientation` normally comes directly from the `orientation` attribute of the configured `tank_capacity` sensor. You can instead provide an orientation entity explicitly:

```yaml
orientation: sensor.house_tank_tank_capacity_orientation
```

The card automatically selects the nearest included tank artwork for the reported capacity. Included horizontal artwork covers 250, 320, 500, 1000, 1500, 2000, and 4000 gallon tanks. Included vertical/manifold artwork covers 50, 120, 240 (2×120), 360 (3×120), and 480 (4×120) gallon configurations.

Fill color defaults to red through 25%, amber through 50%, and green above 50%. A detected delivery is highlighted for up to 24 hours when a delivery timestamp is available, with backward-compatible behavior for the current delivery binary sensor.

## Manual installation
Copy `custom_components/tank_utility_ng` to `/config/custom_components/` and restart Home Assistant.

## Status
Beta. This is an independent community integration and is not affiliated with Tank Utility or Home Assistant.
