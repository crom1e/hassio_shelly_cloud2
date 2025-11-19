"""Light platform for Shelly Cloud 2.

This implementation prepares support for light devices. It relies on the
Cloud 2 status format for lights, which may vary between models. The
entities are only created for devices reported as type "light".
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ColorMode,
    LightEntity,
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
    """Set up Shelly Cloud 2 lights from a config entry."""
    hub: ShellyCloud2Hub = hass.data[DOMAIN][entry.entry_id]
    device_ids: List[str] = entry.options.get(
        CONF_DEVICE_IDS,
        entry.data.get(CONF_DEVICE_IDS, []),
    )

    entities: list[ShellyCloud2Light] = []

    data = hub.data or {}

    for dev_id in device_ids:
        state = data.get(dev_id) or {}
        if state.get("type") != "light":
            continue

        status: Dict[str, Any] = state.get("status", {})
        lights = status.get("lights")
        if isinstance(lights, list) and lights:
            for channel, light in enumerate(lights):
                entities.append(
                    ShellyCloud2Light(
                        hub=hub,
                        device_id=dev_id,
                        channel=channel,
                    )
                )
        else:
            entities.append(
                ShellyCloud2Light(
                    hub=hub,
                    device_id=dev_id,
                    channel=0,
                )
            )

    if entities:
        async_add_entities(entities)


class ShellyCloud2Light(CoordinatorEntity, LightEntity):
    """Representation of a Shelly light channel."""

    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(
        self,
        hub: ShellyCloud2Hub,
        device_id: str,
        channel: int,
    ) -> None:
        """Initialize the light."""
        super().__init__(hub)
        self._hub = hub
        self._device_id = device_id
        self._channel = channel

        state = (hub.data or {}).get(device_id) or {}
        settings = state.get("settings", {})
        dev_type = state.get("type", "light")
        base_name = settings.get("name")
        if not base_name:
            base_name = f"Shelly {dev_type} {device_id}"

        self._attr_name = f"{base_name} Light {channel}"
        self._attr_unique_id = f"shelly_cloud2_{device_id}_light_{channel}"

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        state = (self.coordinator.data or {}).get(self._device_id) or {}
        status = state.get("status", {})
        lights = status.get("lights")
        if isinstance(lights, list) and len(lights) > self._channel:
            return bool(lights[self._channel].get("on"))
        return False

    @property
    def brightness(self) -> int | None:
        """Return brightness in 0-255 scale if available."""
        state = (self.coordinator.data or {}).get(self._device_id) or {}
        status = state.get("status", {})
        lights = status.get("lights")
        if isinstance(lights, list) and len(lights) > self._channel:
            br = lights[self._channel].get("brightness")
            if isinstance(br, (int, float)):
                return max(0, min(255, int(br * 2.55)))
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        color_temp = kwargs.get(ATTR_COLOR_TEMP_KELVIN)

        mode = None
        temperature = None
        cloud_brightness = None

        if color_temp is not None:
            mode = "white"
            temperature = int(color_temp)
        if brightness is not None:
            mode = mode or "white"
            cloud_brightness = int(brightness / 2.55)

        await self._hub.async_set_light(
            device_id=self._device_id,
            channel=self._channel,
            on=True,
            mode=mode,
            temperature=temperature,
            brightness=cloud_brightness,
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        await self._hub.async_set_light(
            device_id=self._device_id,
            channel=self._channel,
            on=False,
        )
        await self.coordinator.async_request_refresh()

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
