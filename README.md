# Shelly Cloud 2 – Home Assistant Integration

This is a Home Assistant custom integration for the Shelly Cloud 2 / Cloud Control HTTP API.
It uses the account-level Authorization cloud key and the Shelly Cloud server host, and can
monitor and control multiple devices under the same account.

- Domain: `shelly_cloud2`
- Configuration: via Home Assistant UI (config flow), no YAML required
- Architecture: one hub per account (server + auth_key + list of device IDs)
- Platforms:
  - `switch` — relay and plug outputs
  - `sensor` — power, energy, temperature, battery, illuminance and diagnostic data
  - `binary_sensor` — door/window state for supported sensor devices

## Installation

[![Quick installation link](https://my.home-assistant.io/badges/hacs_repository.svg)][my-hacs]

Recommended installation is through [HACS][hacs]:

1. Either [use this link][my-hacs], or navigate to HACS integration and:
   - 'Explore & Download Repositories'
   - Search for 'Shelly Cloud 2'
   - Download
2. Restart Home Assistant
3. Go to Settings > Devices and Services > Add Integration
4. Search for and select 'Shelly Cloud 2' (If the integration is not found, empty your browser cache and reload the page)
5. Proceed with the configuration

 


## Sensors per relay/plug device

For each configured relay/plug device (where the data is present), the integration exposes:

Primary sensors:
- Power – from `status.meters[0].power`
  - Unit: W
  - Device class: `power`
  - State class: `measurement`
- Energy – from `status.meters[0].total` (Wh) converted to kWh
  - Unit: kWh
  - Device class: `energy`
  - State class: `total_increasing`
- Temperature – from `status.temperature` or `status.tmp.tC`
  - Unit: °C
  - Device class: `temperature`
  - State class: `measurement`

Diagnostic sensors:
- Wi-Fi signal – from `status.wifi_sta.rssi`
  - Unit: dBm
  - Device class: `signal_strength`
- Uptime – from `status.uptime`
  - Unit: seconds
  - Device class: `duration`
- Last update – from `status._updated` (or `settings._updated`)
  - Device class: `timestamp`

## Door/window sensor devices (e.g. SHDW-2)

For devices reported as type `"sensor"` with door/window capabilities (like Shelly Door/Window 2),
the integration exposes:

Binary sensor:
- Door state – from `status.sensor.state`
  - `"open"` → on (door open)
  - other values (e.g. `"close"`) → off
  - Device class: `door`

Additional sensors:
- Temperature – as above
- Battery – from `status.bat.value`
  - Unit: %
  - Device class: `battery`
  - State class: `measurement`
- Illuminance – from `status.lux.value`
  - Unit: lx
  - Device class: `illuminance`
  - State class: `measurement`
- Wi-Fi signal / Uptime / Last update – as above

All entities belonging to the same Shelly device are grouped under a single Home
Assistant device using the device registry, with identifiers based on the Shelly
device id and model/firmware taken from the Cloud API.
---

[hacs]: https://hacs.xyz
[my-hacs]: https://my.home-assistant.io/redirect/hacs_repository/?owner=crom1e&repository=hassio_shelly_cloud2&category=integration