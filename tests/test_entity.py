"""Tests for entity.py."""

from custom_components.gabb.const import DOMAIN, MANUFACTURER
from custom_components.gabb.entity import GabbBaseEntity


GABB_ID = "device-abc"


def make_entity(coordinator, gabb_id=GABB_ID):
    return GabbBaseEntity(coordinator, gabb_id)


def test_device_data_returns_correct_device(mock_coordinator):
    entity = make_entity(mock_coordinator)
    device = entity.device_data
    assert device is not None
    assert device.gabb_id == GABB_ID


def test_device_data_returns_none_for_unknown_id(mock_coordinator):
    entity = GabbBaseEntity(mock_coordinator, "unknown-id")
    assert entity.device_data is None


def test_device_data_returns_none_when_coordinator_data_is_none(mock_coordinator):
    mock_coordinator.data = None
    entity = make_entity(mock_coordinator)
    assert entity.device_data is None


def test_available_true_when_device_found(mock_coordinator):
    entity = make_entity(mock_coordinator)
    assert entity.available is True


def test_available_false_when_device_missing(mock_coordinator):
    entity = GabbBaseEntity(mock_coordinator, "unknown-id")
    assert entity.available is False


def test_available_false_when_coordinator_not_available(mock_coordinator):
    mock_coordinator.available = False
    entity = make_entity(mock_coordinator)
    assert entity.available is False


def test_device_info_identifiers(mock_coordinator):
    entity = make_entity(mock_coordinator)
    info = entity.device_info
    assert (DOMAIN, GABB_ID) in info.identifiers


def test_device_info_name(mock_coordinator, coordinator_data):
    entity = make_entity(mock_coordinator)
    info = entity.device_info
    expected = coordinator_data.devices[GABB_ID].full_name
    assert info.name == expected


def test_device_info_manufacturer(mock_coordinator):
    entity = make_entity(mock_coordinator)
    info = entity.device_info
    assert info.manufacturer == MANUFACTURER


def test_device_info_model_from_product_name(mock_coordinator, coordinator_data):
    entity = make_entity(mock_coordinator)
    info = entity.device_info
    assert info.model == coordinator_data.devices[GABB_ID].product_name


def test_device_info_model_none_when_empty(mock_coordinator, coordinator_data):
    coordinator_data.devices[GABB_ID].product_name = ""
    entity = make_entity(mock_coordinator)
    info = entity.device_info
    assert info.model is None
