"""The Gabb integration."""

from __future__ import annotations

import logging

import aiohttp

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant

from .api import GabbAPI
from .coordinator import GabbConfigEntry, GabbDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.DEVICE_TRACKER, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: GabbConfigEntry) -> bool:
    """Set up Gabb from a config entry."""
    session = aiohttp.ClientSession()
    api = GabbAPI(
        session,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )

    try:
        await api.login()

        coordinator = GabbDataUpdateCoordinator(hass, api, entry)
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        await session.close()
        raise

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    return True


async def _async_options_updated(
    hass: HomeAssistant, entry: GabbConfigEntry
) -> None:
    """Reload the integration when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: GabbConfigEntry) -> bool:
    """Unload a Gabb config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator: GabbDataUpdateCoordinator = entry.runtime_data
        await coordinator.api.close()

    return unload_ok
