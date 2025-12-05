"""Binary sensor platform for Shelly Cloud 2."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
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
    """Set up Shelly Cloud 2 binary sensors from a config entry."""
    hub: ShellyCloud2Hub = hass.data[DOMAIN][entry.entry_id]
    device_ids: List[str] = entry.options.get(
        CONF_DEVICE_IDS,
        entry.data.get(CONF_DEVICE_IDS, []),
    )

    entities: list[ShellyCloud2DoorSensor] = []

    data = hub.data or {}

    for dev_id in device_ids:
        state = data.get(dev_id) or {}
        if state.get("type") != "sensor":
            continue

        status: Dict[str, Any] = state.get("status", {})
        sensor_block = status.get("sensor")
        if isinstance(sensor_block, dict) and "state" in sensor_block:
            entities.append(
                ShellyCloud2DoorSensor(
                    hub=hub,
                    device_id=dev_id,
                )
            )

    if entities:
        async_add_entities(entities)


class ShellyCloud2DoorSensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Shelly door/window sensor as a binary sensor."""

    _attr_device_class = BinarySensorDeviceClass.DOOR

    def __init__(
        self,
        hub: ShellyCloud2Hub,
        device_id: str,
    ) -> None:
        """Initialize the door sensor."""
        super().__init__(hub)
        self._hub = hub
        self._device_id = device_id

        dev_state = (hub.data or {}).get(device_id) or {}
        dev_type = dev_state.get("type", "sensor")
        base_name = dev_state.get("settings", {}).get("name")
        if not base_name:
            base_name = f"Shelly {dev_type} {device_id}"

        self._device_name = base_name
        self._attr_name = f"{base_name} Door"
        self._attr_unique_id = f"shelly_cloud2_{device_id}_door"

    @property
    def is_on(self) -> bool:
        """Return true if door/window is open."""
        state = (self.coordinator.data or {}).get(self._device_id) or {}
        status = state.get("status", {})
        sensor_block = status.get("sensor")
        if not isinstance(sensor_block, dict):
            return False
        return sensor_block.get("state") == "open"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        state = (self.coordinator.data or {}).get(self._device_id) or {}
        if not state:
            return False
        if state.get("online") == 0:
            return False
        status = state.get("status", {})
        cloud = status.get("cloud", {})
        if isinstance(cloud, dict) and not cloud.get("connected", True):
            return False
        return True

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information for the device registry."""
        state = (self.coordinator.data or {}).get(self._device_id) or {}
        settings = state.get("settings", {})
        dev_type = state.get("type", "sensor")
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
