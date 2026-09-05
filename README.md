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

## HACS installation

1. In HACS, open **Custom repositories**.
2. Add `https://github.com/bronzedragon/home-assistant-tank-utility-ng`.
3. Select **Integration** as the repository type.
4. Open **Tank Utility NG** in HACS and choose **Download**.
5. Restart Home Assistant.
6. Add or manage the integration under **Settings → Devices & services**.

### Migrating an existing manual installation

If Tank Utility NG is already installed manually, do **not** delete its Home Assistant config entry. Back up `/config/custom_components/tank_utility_ng`, then let HACS download the integration over the same component directory and restart Home Assistant. The existing config entry and entities are retained because HACS is changing the code deployment method, not the Home Assistant configuration entry.

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
manifest.json: 0.6.0
GitHub release: v0.6.0
```

## Support

Use the GitHub issue tracker for bug reports and feature requests.

## Status

Beta. This is an independent community integration and is not affiliated with Tank Utility or Home Assistant.
