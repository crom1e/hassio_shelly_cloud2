# Shelly Cloud 2 – Home Assistant Integration

This is a Home Assistant custom integration for the Shelly Cloud 2 / Cloud Control HTTP API.

All values needed for config - API key, cloud URL and sensor IDs are available at http://cloud.shelly.cloud

- Domain: `shelly_cloud2`
- Configuration: via Home Assistant UI (config flow), no YAML required
- Architecture: one hub per account (server + auth_key + list of device IDs)
- Platforms:
  - `switch` — relay and plug outputs
  - `sensor` — power, energy, temperature and diagnostic data

## Sensors per device

For each configured device (where the data is present), the integration exposes:

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

All entities belonging to the same Shelly device are grouped under a single Home
Assistant device using the device registry, with identifiers based on the Shelly
device id and model/firmware taken from the Cloud API.
