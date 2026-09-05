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
- HACS-compatible repository layout

## HACS
Add this repository to HACS as an **Integration**, install **Tank Utility NG**, restart Home Assistant, then add it from **Settings → Devices & services**.

## Manual installation
Copy `custom_components/tank_utility_ng` to `/config/custom_components/` and restart Home Assistant.

## Status
Beta. This is an independent community integration and is not affiliated with Tank Utility or Home Assistant.
