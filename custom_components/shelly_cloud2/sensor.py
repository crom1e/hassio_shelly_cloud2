"""Sensor platform for Shelly Cloud 2."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfEnergy,
    UnitOfPower,
    UnitOfIlluminance,
    UnitOfTemperature,
    UnitOfTime,
    PERCENTAGE, 
    SIGNAL_STRENGTH_DECIBELS,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import ShellyCloud2Hub
from .const import DOMAIN, CONF_DEVICE_IDS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Shelly Cloud 2 sensors from a config entry."""
    hub: ShellyCloud2Hub = hass.data[DOMAIN][entry.entry_id]
    device_ids: List[str] = entry.options.get(
        CONF_DEVICE_IDS,
        entry.data.get(CONF_DEVICE_IDS, []),
    )

    entities: list[ShellyCloud2Sensor] = []

    data = hub.data or {}

    for dev_id in device_ids:
        state = data.get(dev_id) or {}
        status: Dict[str, Any] = state.get("status", {})
        dev_type = state.get("type")

        # Temperature: present if "temperature" or "tmp.tC" exists
        if "temperature" in status or (
            isinstance(status.get("tmp"), dict) and "tC" in status.get("tmp", {})
        ):
            entities.append(
                ShellyCloud2Sensor(
                    hub=hub,
                    device_id=dev_id,
                    kind="temperature",
                    name_suffix="Temperature",
                    device_class=SensorDeviceClass.TEMPERATURE,
                    state_class=SensorStateClass.MEASUREMENT,
                    unit=UnitOfTemperature.CELSIUS,
                    entity_category=None,
                )
            )

        # Power and energy from meters[0]
        meters = status.get("meters")
        if isinstance(meters, list) and meters:
            entities.append(
                ShellyCloud2Sensor(
                    hub=hub,
                    device_id=dev_id,
                    kind="power",
                    name_suffix="Power",
                    device_class=SensorDeviceClass.POWER,
                    state_class=SensorStateClass.MEASUREMENT,
                    unit=UnitOfPower.WATT,
                    entity_category=None,
                )
            )
            entities.append(
                ShellyCloud2Sensor(
                    hub=hub,
                    device_id=dev_id,
                    kind="energy",
                    name_suffix="Energy",
                    device_class=SensorDeviceClass.ENERGY,
                    state_class=SensorStateClass.TOTAL_INCREASING,
                    unit=UnitOfEnergy.KILO_WATT_HOUR,
                    entity_category=None,
                )
            )
        
        # Additional fields for "sensor" type devices (e.g. door/window)

        if dev_type == "sensor":

            # Battery percentage

            bat = status.get("bat")

            if isinstance(bat, dict) and "value" in bat:

                entities.append(

                    ShellyCloud2Sensor(

                        hub=hub,

                        device_id=dev_id,

                        kind="battery",

                        name_suffix="Battery",

                        device_class=SensorDeviceClass.BATTERY,

                        state_class=SensorStateClass.MEASUREMENT,

                        unit=PERCENTAGE,

                        entity_category=None,

                    )

                )



            # Illuminance (lux)

            lux = status.get("lux")

            if isinstance(lux, dict) and "value" in lux:

                entities.append(

                    ShellyCloud2Sensor(

                        hub=hub,

                        device_id=dev_id,

                        kind="illuminance",

                        name_suffix="Illuminance",

                        device_class=SensorDeviceClass.ILLUMINANCE,

                        state_class=SensorStateClass.MEASUREMENT,

                        unit=UnitOfIlluminance.LUX,

                        entity_category=None,

                    )

                )

        # Wi-Fi RSSI
        wifi_sta = status.get("wifi_sta")
        if isinstance(wifi_sta, dict) and "rssi" in wifi_sta:
            entities.append(
                ShellyCloud2Sensor(
                    hub=hub,
                    device_id=dev_id,
                    kind="rssi",
                    name_suffix="Wi-Fi signal",
                    device_class=SensorDeviceClass.SIGNAL_STRENGTH,
                    state_class=SensorStateClass.MEASUREMENT,
                    unit=SIGNAL_STRENGTH_DECIBELS,
                    entity_category=EntityCategory.DIAGNOSTIC,
                )
            )

        # Uptime
        if "uptime" in status:
            entities.append(
                ShellyCloud2Sensor(
                    hub=hub,
                    device_id=dev_id,
                    kind="uptime",
                    name_suffix="Uptime",
                    device_class=SensorDeviceClass.DURATION,
                    state_class=SensorStateClass.MEASUREMENT,
                    unit=UnitOfTime.SECONDS,
                    entity_category=EntityCategory.DIAGNOSTIC,
                )
            )

        # Last update timestamp
        if "_updated" in status or "_updated" in state.get("settings", {}):
            entities.append(
                ShellyCloud2Sensor(
                    hub=hub,
                    device_id=dev_id,
                    kind="last_update",
                    name_suffix="Last update",
                    device_class=SensorDeviceClass.TIMESTAMP,
                    state_class=None,
                    unit=None,
                    entity_category=EntityCategory.DIAGNOSTIC,
                )
            )

    if entities:
        async_add_entities(entities)


class ShellyCloud2Sensor(CoordinatorEntity, SensorEntity):
    """Representation of a Shelly Cloud 2 sensor derived from device status."""

    def __init__(
        self,
        hub: ShellyCloud2Hub,
        device_id: str,
        kind: str,
        name_suffix: str,
        device_class: SensorDeviceClass | None,
        state_class: SensorStateClass | None,
        unit: str | None,
        entity_category: EntityCategory | None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(hub)
        self._hub = hub
        self._device_id = device_id
        self._kind = kind

        dev_state = (hub.data or {}).get(device_id) or {}
        dev_type = dev_state.get("type", "device")
        base_name = dev_state.get("settings", {}).get("name")
        if not base_name:
            base_name = f"Shelly {dev_type} {device_id}"

        self._device_name = base_name
        self._attr_name = f"{base_name} {name_suffix}"
        self._attr_unique_id = f"shelly_cloud2_{device_id}_{kind}"

        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_unit_of_measurement = unit
        self._attr_entity_category = entity_category

    @property
    def native_value(self) -> Any:
        """Return the sensor value based on the coordinator data."""
        state = (self.coordinator.data or {}).get(self._device_id) or {}
        status = state.get("status", {})

        if self._kind == "temperature":
            if "temperature" in status:
                return status.get("temperature")
            tmp = status.get("tmp")
            if isinstance(tmp, Dict):
                return tmp.get("tC")
            return None

        if self._kind in ("power", "energy"):
            meters = status.get("meters")
            if not isinstance(meters, list) or not meters:
                return None
            meter0 = meters[0]
            if self._kind == "power":
                return meter0.get("power")
            if self._kind == "energy":
                total_wh = meter0.get("total")
                if total_wh is None:
                    return None
                try:
                    return float(total_wh) / 1000.0
                except (TypeError, ValueError):
                    return None
            return None
                if self._kind == "battery":

            bat = status.get("bat")

            if not isinstance(bat, Dict):

                return None

            return bat.get("value")

        if self._kind == "illuminance":

            lux = status.get("lux")

            if not isinstance(lux, Dict):

                return None

            return lux.get("value")

        if self._kind == "rssi":
            wifi_sta = status.get("wifi_sta")
            if not isinstance(wifi_sta, Dict):
                return None
            return wifi_sta.get("rssi")

        if self._kind == "uptime":
            return status.get("uptime")

        if self._kind == "last_update":
            ts_str = status.get("_updated")
            if not ts_str:
                ts_str = state.get("settings", {}).get("_updated")
            if not ts_str:
                return None
            try:
                dt_local = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None
            return dt_util.as_utc(dt_local)

        return None

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
        dev_type = state.get("type", "device")
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
