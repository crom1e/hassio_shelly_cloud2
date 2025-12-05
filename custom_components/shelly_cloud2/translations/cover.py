"""Cover platform for Shelly Cloud 2."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from homeassistant.components.cover import (
    CoverEntity,
    CoverEntityFeature,
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
    """Set up Shelly Cloud 2 covers from a config entry."""
    hub: ShellyCloud2Hub = hass.data[DOMAIN][entry.entry_id]
    device_ids: List[str] = entry.options.get(
        CONF_DEVICE_IDS,
        entry.data.get(CONF_DEVICE_IDS, []),
    )

    entities: list[ShellyCloud2Cover] = []

    data = hub.data or {}

    for dev_id in device_ids:
        state = data.get(dev_id) or {}
        if state.get("type") != "cover":
            continue

        status: Dict[str, Any] = state.get("status", {})
        covers = status.get("covers")
        if isinstance(covers, list) and covers:
            for channel, cover in enumerate(covers):
                entities.append(
                    ShellyCloud2Cover(
                        hub=hub,
                        device_id=dev_id,
                        channel=channel,
                    )
                )
        else:
            entities.append(
                ShellyCloud2Cover(
                    hub=hub,
                    device_id=dev_id,
                    channel=0,
                )
            )

    if entities:
        async_add_entities(entities)


class ShellyCloud2Cover(CoordinatorEntity, CoverEntity):
    """Representation of a Shelly cover channel."""

    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION
    )

    def __init__(
        self,
        hub: ShellyCloud2Hub,
        device_id: str,
        channel: int,
    ) -> None:
        """Initialize the cover."""
        super().__init__(hub)
        self._hub = hub
        self._device_id = device_id
        self._channel = channel

        state = (hub.data or {}).get(device_id) or {}
        settings = state.get("settings", {})
        dev_type = state.get("type", "cover")
        base_name = settings.get("name")
        if not base_name:
            base_name = f"Shelly {dev_type} {device_id}"

        self._attr_name = f"{base_name} Cover {channel}"
        self._attr_unique_id = f"shelly_cloud2_{device_id}_cover_{channel}"

    @property
    def current_cover_position(self) -> int | None:
        """Return the current position of the cover as a percentage."""
        state = (self.coordinator.data or {}).get(self._device_id) or {}
        status = state.get("status", {})
        covers = status.get("covers")
        if isinstance(covers, list) and len(covers) > self._channel:
            pos = covers[self._channel].get("position")
            if isinstance(pos, (int, float)):
                return int(pos)
        return None

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed."""
        position = self.current_cover_position
        if position is None:
            return None
        return position == 0

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self._hub.async_set_cover(
            device_id=self._device_id,
            channel=self._channel,
            position="open",
        )
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        await self._hub.async_set_cover(
            device_id=self._device_id,
            channel=self._channel,
            position="close",
        )
        await self.coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        await self._hub.async_set_cover(
            device_id=self._device_id,
            channel=self._channel,
            position="stop",
        )
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Set the cover position."""
        position = kwargs.get("position")
        if position is None:
            return
        await self._hub.async_set_cover(
            device_id=self._device_id,
            channel=self._channel,
            position=int(position),
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
