"""Switch platform for Shelly Cloud 2."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ShellyCloud2Hub
from .const import DOMAIN, CONF_DEVICE_IDS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Shelly Cloud 2 switches from a config entry."""
    hub: ShellyCloud2Hub = hass.data[DOMAIN][entry.entry_id]
    device_ids: List[str] = entry.options.get(
        CONF_DEVICE_IDS,
        entry.data.get(CONF_DEVICE_IDS, []),
    )

    entities: list[ShellyCloud2Switch] = []

    data = hub.data or {}

    for dev_id in device_ids:
        state = data.get(dev_id) or {}
        if state.get("type") != "relay":
            continue

        status: Dict[str, Any] = state.get("status", {})
        relays = status.get("relays")
        if not isinstance(relays, list):
            continue

        for channel, relay in enumerate(relays):
            entities.append(
                ShellyCloud2Switch(
                    hub=hub,
                    device_id=dev_id,
                    channel=channel,
                )
            )

    if entities:
        async_add_entities(entities)


class ShellyCloud2Switch(CoordinatorEntity, SwitchEntity):
    """Representation of a Shelly relay channel as a switch."""

    def __init__(
        self,
        hub: ShellyCloud2Hub,
        device_id: str,
        channel: int,
    ) -> None:
        """Initialize the switch."""
        super().__init__(hub)
        self._hub = hub
        self._device_id = device_id
        self._channel = channel

        state = (hub.data or {}).get(device_id) or {}
        settings = state.get("settings", {})
        dev_type = state.get("type", "relay")
        base_name = settings.get("name")
        if not base_name:
            base_name = f"Shelly {dev_type} {device_id}"

        self._device_name = base_name

        relays = state.get("status", {}).get("relays", [])
        if len(relays) > 1:
            name = f"{base_name} Relay {channel}"
        else:
            name = base_name

        self._attr_name = name
        self._attr_unique_id = f"shelly_cloud2_{device_id}_relay_{channel}"

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        state = (self.coordinator.data or {}).get(self._device_id) or {}
        status = state.get("status", {})
        relays = status.get("relays")
        if not isinstance(relays, list):
            return False
        try:
            relay = relays[self._channel]
        except IndexError:
            return False
        return bool(relay.get("ison"))

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        state = (self.coordinator.data or {}).get(self._device_id) or {}
        if not state:
            return False
        if state.get("online") == 0:
            return False
        cloud = state.get("status", {}).get("cloud", {})
        if isinstance(cloud, dict) and not cloud.get("connected", True):
            return False
        return True

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._hub.async_set_switch(
            device_id=self._device_id,
            channel=self._channel,
            on=True,
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._hub.async_set_switch(
            device_id=self._device_id,
            channel=self._channel,
            on=False,
        )
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information for the device registry."""
        state = (self.coordinator.data or {}).get(self._device_id) or {}
        settings = state.get("settings", {})
        dev_type = state.get("type", "relay")
        base_name = settings.get("name") or self._device_name
        device_meta = settings.get("device", {})
        model = device_meta.get("type") or state.get("code") or dev_type
        fw = (
            state.get("status", {})
            .get("getinfo", {})
            .get("fw_info", {})
            .get("fw")
        )
        info: Dict[str, Any] = {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": base_name,
            "manufacturer": "Shelly",
            "model": model,
        }
        if fw:
            info["sw_version"] = fw
        return info
