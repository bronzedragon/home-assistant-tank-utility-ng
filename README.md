# Tank Utility NG

A modern Home Assistant custom integration for Tank Utility propane tank monitors.

## Features

- UI configuration and options flows
- Tank level, temperature, capacity, and orientation
- Average consumption and estimated refill date
- Gallons remaining and propane kWh equivalence
- Energy Dashboard-compatible cumulative gas and energy sensors
- Delivery detection and delivery-volume estimation groundwork
- Battery and Wi-Fi telemetry diagnostics
- Automatic temperature and volume-unit handling
- Conservative configurable polling for Tank Utility API rate limits
- Entity-ID migration guidance
- Local Home Assistant brand icon support
- HACS-managed installation and updates
- **Included `tank-utility-ng-gauge` Lovelace card** with capacity/orientation-aware tank artwork, static fill level, gauge colors, and delivery highlighting

## HACS installation

1. In HACS, open **Custom repositories**.
2. Add `https://github.com/bronzedragon/home-assistant-tank-utility-ng`.
3. Select **Integration** as the repository type.
4. Open **Tank Utility NG** in HACS and choose **Download**.
5. Restart Home Assistant.
6. Add or manage the integration under **Settings → Devices & services**.

The integration serves and registers its bundled Lovelace card automatically when Lovelace resources are storage-managed. If your Lovelace resources are YAML-managed, add `/tank_utility_ng/frontend/tank-utility-ng-gauge.js` as a JavaScript module manually.

### Migrating an existing manual installation

If Tank Utility NG is already installed manually, do **not** delete its Home Assistant config entry. Back up `/config/custom_components/tank_utility_ng`, then let HACS download the integration over the same component directory and restart Home Assistant. The existing config entry and entities are retained because HACS is changing the code deployment method, not the Home Assistant configuration entry.

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

Manual installation remains possible for development and recovery:

1. Copy `custom_components/tank_utility_ng` to `/config/custom_components/`.
2. Restart Home Assistant.
3. Add the integration from **Settings → Devices & services**.

For normal use, HACS is the recommended installation and update method.

## Versioning

GitHub releases use tags matching the integration version in `manifest.json`.

Example:

```text
manifest.json: 0.6.2
GitHub release: v0.6.2
```

## Support

Use the GitHub issue tracker for bug reports and feature requests.

## Status

Beta. This is an independent community integration and is not affiliated with Tank Utility or Home Assistant.
