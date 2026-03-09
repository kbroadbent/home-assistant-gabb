"""Diagnostics support for the Gabb integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import GabbDataUpdateCoordinator

TO_REDACT = {
    "access_token",
    "refresh_token",
    "password",
    "latitude",
    "longitude",
    "username",
    "imei",
    "gabb_id",
    "family_id",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: GabbDataUpdateCoordinator = entry.runtime_data
    data = coordinator.data

    devices_raw: dict[str, Any] = {}
    if data:
        for gabb_id, device in data.devices.items():
            devices_raw[gabb_id] = device.raw_data

    return async_redact_data(
        {
            "config_entry": entry.as_dict(),
            "device_count": len(data.devices) if data else 0,
            "devices": devices_raw,
        },
        TO_REDACT,
    )
