"""DataUpdateCoordinator for the Gabb integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GabbAPI
from .const import CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, DOMAIN
from .exceptions import GabbAuthError, GabbConnectionError
from .models import GabbCoordinatorData

_LOGGER = logging.getLogger(__name__)

type GabbConfigEntry = ConfigEntry[GabbDataUpdateCoordinator]


class GabbDataUpdateCoordinator(DataUpdateCoordinator[GabbCoordinatorData]):
    """Coordinator to fetch Gabb device data."""

    config_entry: GabbConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        api: GabbAPI,
        entry: GabbConfigEntry,
    ) -> None:
        interval = entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )
        self.api = api

    async def _async_update_data(self) -> GabbCoordinatorData:
        """Fetch data from the Gabb API."""
        try:
            locations, device_infos = await self._fetch_data()
        except GabbAuthError:
            try:
                await self.api.refresh_access_token()
                locations, device_infos = await self._fetch_data()
            except GabbAuthError as err:
                raise ConfigEntryAuthFailed(
                    f"Authentication failed: {err}"
                ) from err
        except GabbConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

        return GabbCoordinatorData.from_api_responses(locations, device_infos)

    async def _fetch_data(self) -> tuple[list, list]:
        """Fetch both locations and device info."""
        locations = await self.api.get_locations()
        device_infos = await self.api.get_devices()
        return locations, device_infos
