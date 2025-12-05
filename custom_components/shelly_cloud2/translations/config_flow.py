"""Config flow for Shelly Cloud 2 integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, CONF_SERVER, CONF_AUTH_KEY, CONF_DEVICE_IDS

_LOGGER = logging.getLogger(__name__)


def _parse_device_ids(raw: str) -> list[str]:
    """Parse a comma/newline-separated list of device IDs."""
    if raw is None:
        return []
    parts = raw.replace("\n", ",").split(",")
    return [p.strip() for p in parts if p.strip()]


def _device_ids_to_text(ids: list[str] | None) -> str:
    """Render device IDs list into a comma-separated string for the form."""
    if not ids:
        return ""
    return ", ".join(ids)


def _build_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Build the data entry schema for the user step."""
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_SERVER, default=defaults.get(CONF_SERVER, "")): str,
            vol.Required(CONF_AUTH_KEY, default=defaults.get(CONF_AUTH_KEY, "")): str,
            vol.Required(
                CONF_DEVICE_IDS,
                default=defaults.get(CONF_DEVICE_IDS, ""),
            ): str,
        }
    )


class ShellyCloud2ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Shelly Cloud 2."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            server = user_input[CONF_SERVER].strip()
            auth_key = user_input[CONF_AUTH_KEY].strip()
            raw_ids = user_input[CONF_DEVICE_IDS]

            device_ids = _parse_device_ids(raw_ids)

            if not server:
                errors["base"] = "invalid_server"
            elif not auth_key:
                errors["base"] = "invalid_auth"
            elif not device_ids:
                errors["base"] = "no_devices"
            else:
                return self.async_create_entry(
                    title=f"Shelly Cloud 2 ({server})",
                    data={
                        CONF_SERVER: server,
                        CONF_AUTH_KEY: auth_key,
                        CONF_DEVICE_IDS: device_ids,
                    },
                )

        defaults: dict[str, Any] = {}
        if user_input is not None:
            defaults = dict(user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(defaults),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow handler."""
        return ShellyCloud2OptionsFlow(config_entry)


class ShellyCloud2OptionsFlow(config_entries.OptionsFlow):
    """Handle Shelly Cloud 2 options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize ShellyCloud2OptionsFlow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage the options for device IDs."""
        errors: dict[str, str] = {}

        current_ids: list[str] = self.config_entry.options.get(
            CONF_DEVICE_IDS,
            self.config_entry.data.get(CONF_DEVICE_IDS, []),
        )

        if user_input is not None:
            raw_ids = user_input[CONF_DEVICE_IDS]
            device_ids = _parse_device_ids(raw_ids)
            if not device_ids:
                errors["base"] = "no_devices"
            else:
                return self.async_create_entry(
                    title="",
                    data={CONF_DEVICE_IDS: device_ids},
                )

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_DEVICE_IDS,
                    default=_device_ids_to_text(current_ids),
                ): str
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )
