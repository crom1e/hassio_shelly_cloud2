"""Shelly Cloud 2 integration entrypoint."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any, Dict, List

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    CONF_SERVER,
    CONF_AUTH_KEY,
    CONF_DEVICE_IDS,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH, Platform.BINARY_SENSOR]


class ShellyCloud2Hub(DataUpdateCoordinator[Dict[str, Any]]):
    """Coordinator that manages communication with Shelly Cloud 2."""

    def __init__(
        self,
        hass: HomeAssistant,
        server: str,
        auth_key: str,
        device_ids: List[str],
    ) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.server = server.strip()
        self.auth_key = auth_key
        self.device_ids = device_ids

        if self.server.startswith("http://") or self.server.startswith("https://"):
            self._base_url = self.server.rstrip("/")
        else:
            self._base_url = f"https://{self.server.rstrip('/')}"

        self._session = async_get_clientsession(hass)

        super().__init__(
            hass,
            _LOGGER,
            name=f"Shelly Cloud 2 ({self._base_url})",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    @property
    def base_url(self) -> str:
        """Return the base URL used for API calls."""
        return self._base_url

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch state for all configured devices.

        Returns a mapping device_id -> state object from the Cloud API.
        """
        if not self.device_ids:
            return {}

        states: Dict[str, Any] = {}
        chunk_size = 10
        for i in range(0, len(self.device_ids), chunk_size):
            chunk = self.device_ids[i : i + chunk_size]
            body = {
                "ids": chunk,
                "select": ["status", "settings"],
            }
            url = f"{self._base_url}/v2/devices/api/get"
            params = {"auth_key": self.auth_key}
            try:
                async with self._session.post(
                    url, params=params, json=body, timeout=15
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        raise UpdateFailed(
                            f"Error {resp.status} fetching devices state: {text}"
                        )
                    data = await resp.json()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                raise UpdateFailed(f"Error fetching devices state: {exc}") from exc

            if not isinstance(data, list):
                raise UpdateFailed("Unexpected response format from Shelly Cloud API")

            for dev_state in data:
                dev_id = dev_state.get("id")
                if dev_id:
                    states[dev_id] = dev_state

        return states

    async def async_set_switch(
        self,
        device_id: str,
        channel: int,
        on: bool,
        toggle_after: int | None = None,
    ) -> None:
        """Control a switch output on a device."""
        url = f"{self._base_url}/v2/devices/api/set/switch"
        params = {"auth_key": self.auth_key}
        body: Dict[str, Any] = {
            "id": device_id,
            "channel": channel,
            "on": on,
        }
        if toggle_after is not None:
            body["toggle_after"] = toggle_after

        try:
            async with self._session.post(
                url, params=params, json=body, timeout=15
            ) as resp:
                text = await resp.text()
                if resp.status != 200:
                    raise UpdateFailed(
                        f"Control command failed with HTTP {resp.status}: {text}"
                    )
                if text:
                    try:
                        data = await resp.json()
                    except Exception:
                        data = None
                    if isinstance(data, dict) and "error" in data:
                        messages = data.get("data", {}).get("messages", [])
                        raise UpdateFailed(
                            f"Control command error: {data['error']} messages={messages}"
                        )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            raise UpdateFailed(f"Error sending control command: {exc}") from exc


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Shelly Cloud 2 component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Shelly Cloud 2 from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    server: str = entry.data[CONF_SERVER]
    auth_key: str = entry.data[CONF_AUTH_KEY]
    device_ids = entry.options.get(CONF_DEVICE_IDS, entry.data.get(CONF_DEVICE_IDS, []))
    if not isinstance(device_ids, list):
        device_ids = []

    hub = ShellyCloud2Hub(
        hass=hass,
        server=server,
        auth_key=auth_key,
        device_ids=device_ids,
    )
    hass.data[DOMAIN][entry.entry_id] = hub

    await hub.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
