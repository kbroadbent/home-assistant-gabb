"""Tests for device_tracker.py."""

from unittest.mock import MagicMock

import pytest

from custom_components.gabb.device_tracker import GabbDeviceTracker, async_setup_entry
from custom_components.gabb.models import GabbDeviceData
from homeassistant.components.device_tracker import SourceType
from homeassistant.config_entries import ConfigEntry


GABB_ID = "device-abc"


def make_tracker(coordinator, gabb_id=GABB_ID):
    return GabbDeviceTracker(coordinator, gabb_id)


def test_unique_id(mock_coordinator):
    tracker = make_tracker(mock_coordinator)
    assert tracker._attr_unique_id == f"{GABB_ID}_tracker"


def test_source_type(mock_coordinator):
    tracker = make_tracker(mock_coordinator)
    assert tracker.source_type == SourceType.GPS


def test_latitude(mock_coordinator, coordinator_data):
    tracker = make_tracker(mock_coordinator)
    assert tracker.latitude == coordinator_data.devices[GABB_ID].latitude


def test_longitude(mock_coordinator, coordinator_data):
    tracker = make_tracker(mock_coordinator)
    assert tracker.longitude == coordinator_data.devices[GABB_ID].longitude


def test_latitude_none_when_device_not_found(mock_coordinator):
    tracker = GabbDeviceTracker(mock_coordinator, "unknown-id")
    assert tracker.latitude is None


def test_longitude_none_when_device_not_found(mock_coordinator):
    tracker = GabbDeviceTracker(mock_coordinator, "unknown-id")
    assert tracker.longitude is None


def test_location_accuracy(mock_coordinator, coordinator_data):
    tracker = make_tracker(mock_coordinator)
    assert tracker.location_accuracy == int(coordinator_data.devices[GABB_ID].accuracy)


def test_location_accuracy_zero_when_accuracy_none(mock_coordinator, coordinator_data):
    coordinator_data.devices[GABB_ID].accuracy = None
    tracker = make_tracker(mock_coordinator)
    assert tracker.location_accuracy == 0


def test_location_accuracy_zero_when_no_device(mock_coordinator):
    tracker = GabbDeviceTracker(mock_coordinator, "unknown-id")
    assert tracker.location_accuracy == 0


def test_extra_state_attributes(mock_coordinator, coordinator_data):
    tracker = make_tracker(mock_coordinator)
    attrs = tracker.extra_state_attributes
    device = coordinator_data.devices[GABB_ID]
    assert attrs["altitude"] == device.altitude
    assert attrs["speed"] == device.speed
    assert attrs["imei"] == device.imei


def test_extra_state_attributes_empty_when_no_device(mock_coordinator):
    tracker = GabbDeviceTracker(mock_coordinator, "unknown-id")
    assert tracker.extra_state_attributes == {}


def test_name_is_none(mock_coordinator):
    tracker = make_tracker(mock_coordinator)
    assert tracker._attr_name is None


async def test_setup_entry_creates_trackers(mock_coordinator):
    entry = ConfigEntry()
    entry.runtime_data = mock_coordinator
    async_add_entities = MagicMock()
    await async_setup_entry(MagicMock(), entry, async_add_entities)
    async_add_entities.assert_called_once()
    entities = list(async_add_entities.call_args[0][0])
    assert len(entities) == 1
    assert isinstance(entities[0], GabbDeviceTracker)
    assert entities[0]._attr_unique_id == f"{GABB_ID}_tracker"


async def test_setup_entry_registers_listener(mock_coordinator):
    entry = ConfigEntry()
    entry.runtime_data = mock_coordinator
    async_add_entities = MagicMock()
    await async_setup_entry(MagicMock(), entry, async_add_entities)
    assert len(mock_coordinator._listeners) == 1


async def test_setup_entry_dynamic_discovery(mock_coordinator, coordinator_data):
    entry = ConfigEntry()
    entry.runtime_data = mock_coordinator
    async_add_entities = MagicMock()

    await async_setup_entry(MagicMock(), entry, async_add_entities)

    new_device = GabbDeviceData(
        gabb_id="new-device-xyz",
        latitude=1.0,
        longitude=2.0,
        accuracy=None,
        altitude=None,
        speed=None,
        battery_level=None,
        timestamp=None,
        created_at=None,
    )
    coordinator_data.devices["new-device-xyz"] = new_device

    listener = mock_coordinator._listeners[0]
    listener()

    assert async_add_entities.call_count == 2
    new_entities = list(async_add_entities.call_args[0][0])
    assert len(new_entities) == 1
    assert new_entities[0]._attr_unique_id == "new-device-xyz_tracker"


async def test_setup_entry_listener_noop_when_data_none(mock_coordinator, coordinator_data):
    entry = ConfigEntry()
    entry.runtime_data = mock_coordinator
    async_add_entities = MagicMock()

    await async_setup_entry(MagicMock(), entry, async_add_entities)

    mock_coordinator.data = None
    listener = mock_coordinator._listeners[0]
    listener()

    assert async_add_entities.call_count == 1
