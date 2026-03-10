"""Tests for coordinator.py."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.gabb.const import CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
from custom_components.gabb.coordinator import GabbDataUpdateCoordinator
from custom_components.gabb.exceptions import GabbAuthError, GabbConnectionError
from custom_components.gabb.models import GabbCoordinatorData
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.config_entries import ConfigEntry


@pytest.fixture
def api():
    return AsyncMock()


def make_coordinator(api, config_entry, hass=None):
    return GabbDataUpdateCoordinator(
        hass=hass or MagicMock(),
        api=api,
        entry=config_entry,
    )


async def test_successful_update(api, config_entry, location_response, device_response):
    api.get_locations.return_value = location_response
    api.get_devices.return_value = device_response
    coordinator = make_coordinator(api, config_entry)
    result = await coordinator._async_update_data()
    assert isinstance(result, GabbCoordinatorData)
    assert "device-abc" in result.devices


async def test_auth_error_refreshes_and_retries(api, config_entry, location_response, device_response):
    api.get_locations.side_effect = [GabbAuthError("auth failed"), location_response]
    api.get_devices.return_value = device_response
    coordinator = make_coordinator(api, config_entry)
    result = await coordinator._async_update_data()
    api.refresh_access_token.assert_called_once()
    assert isinstance(result, GabbCoordinatorData)


async def test_auth_error_on_retry_raises_config_entry_auth_failed(api, config_entry):
    api.get_locations.side_effect = [GabbAuthError("first"), GabbAuthError("second")]
    api.get_devices.return_value = []
    coordinator = make_coordinator(api, config_entry)
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


async def test_connection_error_on_retry_raises_update_failed(api, config_entry, device_response):
    api.get_locations.side_effect = [GabbAuthError("first"), GabbConnectionError("retry")]
    api.get_devices.return_value = device_response
    coordinator = make_coordinator(api, config_entry)
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_connection_error_on_first_fetch_raises_update_failed(api, config_entry):
    api.get_locations.side_effect = GabbConnectionError("network down")
    coordinator = make_coordinator(api, config_entry)
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_generic_error_raises_update_failed(api, config_entry):
    api.get_locations.side_effect = RuntimeError("unexpected")
    coordinator = make_coordinator(api, config_entry)
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


def test_update_interval_from_options(api):
    entry = ConfigEntry(options={CONF_UPDATE_INTERVAL: 120})
    coordinator = make_coordinator(api, entry)
    assert coordinator.update_interval == timedelta(seconds=120)


def test_update_interval_default_when_not_set(api, config_entry):
    coordinator = make_coordinator(api, config_entry)
    assert coordinator.update_interval == timedelta(seconds=DEFAULT_UPDATE_INTERVAL)
