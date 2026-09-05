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
- **Included `tank-utility-ng-gauge` Lovelace card** with capacity/orientation-aware tank artwork, static fill level, gauge colors, delivery highlighting, history access, and Energy Dashboard navigation

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

## Energy Dashboard

Tank Utility NG exposes three cumulative consumption views derived from the same propane usage total:

- **Propane Consumption** — gallons, `state_class: total_increasing`; useful for propane-specific statistics and history.
- **Gas Consumption** — cubic feet, `device_class: gas`, `state_class: total_increasing`; this is the recommended entity for Home Assistant's native **Gas consumption** section on the Energy Dashboard.
- **Energy Consumption** — kWh propane-energy equivalent, `device_class: energy`, `state_class: total_increasing`; useful for energy-equivalent statistics and comparisons, but normally should not also be added as an Energy Dashboard electrical device when the Gas Consumption entity is already representing the same fuel use.

`Energy Remaining` is an inventory estimate derived from gallons remaining. It intentionally has no cumulative state class and is not an Energy Dashboard consumption source.

The integration's cumulative meter survives Home Assistant restarts. Delivery events reset the accepted tank-level baseline without reducing the cumulative usage total. Small upward tank-level movements that do not qualify as a delivery are ignored for the consumption baseline so ordinary gauge/temperature jitter is not counted twice when the level returns downward.

Configure the Energy Dashboard under **Settings → Dashboards → Energy** and select the Tank Utility NG **Gas Consumption** entity as a gas source. Let Home Assistant provide the native long-term charts, period comparisons, and Energy cost UX rather than duplicating them inside the custom tank card.

## Included Lovelace card

Minimum configuration:

```yaml
type: custom:tank-utility-ng-gauge
tank_level: sensor.tank_level
gallons_remaining: sensor.gallons_remaining
tank_capacity: sensor.tank_capacity
delivery: binary_sensor.delivery_detected
```

`orientation` normally comes directly from the `orientation` attribute of the configured `tank_capacity` sensor. You can instead provide an orientation entity explicitly:

```yaml
orientation: sensor.tank_orientation
```

The card automatically selects the nearest included tank artwork for the reported capacity. Included horizontal artwork covers 250, 320, 500, 1000, 1500, 2000, and 4000 gallon tanks. Included vertical/manifold artwork covers 50, 120, 240 (2×120), 360 (3×120), and 480 (4×120) gallon configurations.

Fill color defaults to red through 25%, amber through 50%, and green above 50%. A detected delivery is highlighted for up to 24 hours when a delivery timestamp is available, with backward-compatible behavior for the current delivery binary sensor.

### Energy/history-aware card configuration

The gauge does not duplicate Home Assistant's native Energy charts. Instead, optional consumption entities add compact summary values and an **Energy** navigation button, while **History** opens Home Assistant's native more-info/history UI.

```yaml
type: custom:tank-utility-ng-gauge
tank_level: sensor.tank_level
gallons_remaining: sensor.gallons_remaining
tank_capacity: sensor.tank_capacity
delivery: binary_sensor.delivery_detected
average_consumption: sensor.average_consumption
gas_consumption: sensor.gas_consumption
energy_consumption: sensor.energy_consumption
energy_remaining: sensor.energy_remaining
# Optional, if you maintain a separate cost entity:
# cost: sensor.gas_consumption_cost
```

Optional interaction settings:

```yaml
# Entity shown by the History button. Defaults to gas_consumption,
# then energy_consumption, then tank_level.
history_entity: sensor.gas_consumption

# Defaults to /energy.
energy_dashboard_path: /energy

# Hide the Energy button even when a consumption entity is configured.
show_energy_link: true

# Tapping the tank defaults to more-info for tank_level.
tap_action:
  action: more-info
  entity: sensor.tank_level
```

Supported `tap_action` values are `more-info`, `navigate`, `url`, and `none`. For `navigate`, provide `navigation_path`; for `url`, provide `url_path`.

All entity IDs are card configuration. The bundled JavaScript does not depend on a specific tank name or on `house_tank` entity IDs.

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
manifest.json: 0.6.3
GitHub release: v0.6.3
```

## Support

Use the GitHub issue tracker for bug reports and feature requests.

## Status

Beta. This is an independent community integration and is not affiliated with Tank Utility or Home Assistant.
