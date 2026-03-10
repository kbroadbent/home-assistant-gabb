"""Tests for sensor.py."""

from unittest.mock import MagicMock

import pytest

from custom_components.gabb.models import GabbDeviceData
from custom_components.gabb.sensor import GabbBatterySensor, async_setup_entry
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry


GABB_ID = "device-abc"


def make_sensor(coordinator, gabb_id=GABB_ID):
    return GabbBatterySensor(coordinator, gabb_id)


def test_unique_id(mock_coordinator):
    sensor = make_sensor(mock_coordinator)
    assert sensor._attr_unique_id == f"{GABB_ID}_battery"


def test_native_value(mock_coordinator, coordinator_data):
    sensor = make_sensor(mock_coordinator)
    assert sensor.native_value == coordinator_data.devices[GABB_ID].battery_level


def test_native_value_none_when_device_not_found(mock_coordinator):
    sensor = GabbBatterySensor(mock_coordinator, "unknown-id")
    assert sensor.native_value is None


def test_device_class(mock_coordinator):
    sensor = make_sensor(mock_coordinator)
    assert sensor._attr_device_class == SensorDeviceClass.BATTERY


def test_native_unit(mock_coordinator):
    sensor = make_sensor(mock_coordinator)
    assert sensor._attr_native_unit_of_measurement == "%"


def test_state_class(mock_coordinator):
    sensor = make_sensor(mock_coordinator)
    assert sensor._attr_state_class == SensorStateClass.MEASUREMENT


def test_name(mock_coordinator):
    sensor = make_sensor(mock_coordinator)
    assert sensor._attr_name == "Battery"


async def test_setup_entry_creates_sensors(mock_coordinator):
    entry = ConfigEntry()
    entry.runtime_data = mock_coordinator
    async_add_entities = MagicMock()
    await async_setup_entry(MagicMock(), entry, async_add_entities)
    async_add_entities.assert_called_once()
    entities = list(async_add_entities.call_args[0][0])
    assert len(entities) == 1
    assert isinstance(entities[0], GabbBatterySensor)
    assert entities[0]._attr_unique_id == f"{GABB_ID}_battery"


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

    # Add a new device to the coordinator data
    new_device = GabbDeviceData(
        gabb_id="new-device-xyz",
        latitude=None,
        longitude=None,
        accuracy=None,
        altitude=None,
        speed=None,
        battery_level=50,
        timestamp=None,
        created_at=None,
    )
    coordinator_data.devices["new-device-xyz"] = new_device

    # Trigger the registered listener
    listener = mock_coordinator._listeners[0]
    listener()

    assert async_add_entities.call_count == 2
    new_entities = list(async_add_entities.call_args[0][0])
    assert len(new_entities) == 1
    assert new_entities[0]._attr_unique_id == "new-device-xyz_battery"


async def test_setup_entry_listener_noop_when_data_none(mock_coordinator, coordinator_data):
    entry = ConfigEntry()
    entry.runtime_data = mock_coordinator
    async_add_entities = MagicMock()

    await async_setup_entry(MagicMock(), entry, async_add_entities)

    # Set coordinator data to None then trigger listener
    mock_coordinator.data = None
    listener = mock_coordinator._listeners[0]
    listener()

    assert async_add_entities.call_count == 1
