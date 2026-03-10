"""Tests for diagnostics.py."""

from unittest.mock import MagicMock

import pytest

from custom_components.gabb.diagnostics import async_get_config_entry_diagnostics
from custom_components.gabb.models import GabbCoordinatorData


async def test_output_contains_config_entry_key(config_entry, coordinator_data):
    coord = MagicMock()
    coord.data = coordinator_data
    config_entry.runtime_data = coord

    result = await async_get_config_entry_diagnostics(MagicMock(), config_entry)
    assert "config_entry" in result


async def test_device_count_is_accurate(config_entry, coordinator_data):
    coord = MagicMock()
    coord.data = coordinator_data
    config_entry.runtime_data = coord

    result = await async_get_config_entry_diagnostics(MagicMock(), config_entry)
    assert result["device_count"] == 1


async def test_devices_key_present(config_entry, coordinator_data):
    coord = MagicMock()
    coord.data = coordinator_data
    config_entry.runtime_data = coord

    result = await async_get_config_entry_diagnostics(MagicMock(), config_entry)
    assert "devices" in result


async def test_sensitive_fields_are_redacted(config_entry, coordinator_data):
    coord = MagicMock()
    coord.data = coordinator_data
    config_entry.runtime_data = coord

    result = await async_get_config_entry_diagnostics(MagicMock(), config_entry)

    # Config entry data fields
    assert result["config_entry"]["data"]["password"] == "**REDACTED**"
    assert result["config_entry"]["data"]["username"] == "**REDACTED**"

    # Device raw_data fields
    device_raw = result["devices"]["device-abc"]
    assert device_raw["latitude"] == "**REDACTED**"
    assert device_raw["longitude"] == "**REDACTED**"
    assert device_raw["imei"] == "**REDACTED**"
    assert device_raw["gabb_id"] == "**REDACTED**"


async def test_non_sensitive_fields_not_redacted(config_entry, coordinator_data):
    coord = MagicMock()
    coord.data = coordinator_data
    config_entry.runtime_data = coord

    result = await async_get_config_entry_diagnostics(MagicMock(), config_entry)

    device_raw = result["devices"]["device-abc"]
    assert device_raw["battery_level"] == 85
    assert device_raw["speed"] == 0.0
    assert device_raw["altitude"] == 5.0


async def test_coordinator_data_none_gives_zero_count(config_entry):
    coord = MagicMock()
    coord.data = None
    config_entry.runtime_data = coord

    result = await async_get_config_entry_diagnostics(MagicMock(), config_entry)
    assert result["device_count"] == 0
    assert result["devices"] == {}
