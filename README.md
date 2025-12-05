# Shelly Cloud APIv2 – Home Assistant Integration

This is a Home Assistant custom integration for the Shelly Cloud / Cloud Control HTTP API v2

It uses the account-level Authorization cloud key and the Shelly Cloud server host, and can monitor and control multiple devices under the same account.

Architecture: one hub per account (server + auth_key + list of device IDs)

## Installation

[![Quick installation link](https://my.home-assistant.io/badges/hacs_repository.svg)][my-hacs]

Recommended installation is through [HACS][hacs]:

1. Either [use this link][my-hacs], or navigate to HACS integration and:
   - 'Explore & Download Repositories'
   - Search for 'Shelly Cloud 2'
   - Download
2. Restart Home Assistant
3. Go to Settings > Devices and Services > Add Integration
4. Search for and select 'Shelly Cloud 2' 
5. Proceed with the configuration
6. Cloud Key and Server Host are available in the [Shelly Cloud][shellycloud], Settings, User Settings, Authorizatin Cloud Key, Get Key
7. Device IDs are found on the Device Information in the Settings Pane for each device. Multiple devices are separated by newline or , 

Additional devices can be added later by expanding the list of devices. 
---

[shellycloud]: https://control.shelly.cloud/
[hacs]: https://hacs.xyz
[my-hacs]: https://my.home-assistant.io/redirect/hacs_repository/?owner=crom1e&repository=hassio_shelly_cloud2&category=integration