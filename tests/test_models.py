"""Tests for models.py."""

import pytest

from custom_components.gabb.models import (
    GabbCoordinatorData,
    GabbDeviceData,
    GabbDeviceInfo,
)


# ---------------------------------------------------------------------------
# GabbDeviceInfo
# ---------------------------------------------------------------------------


def test_device_info_full_fields():
    data = {
        "gabb_id": "device-abc",
        "first_name": "Alex",
        "last_name": "Smith",
        "productName": "Gabb Watch 3",
        "sku": "GW3",
        "imei": "123456789012345",
        "status": "active",
    }
    info = GabbDeviceInfo.from_api_response(data)
    assert info.gabb_id == "device-abc"
    assert info.first_name == "Alex"
    assert info.last_name == "Smith"
    assert info.product_name == "Gabb Watch 3"
    assert info.sku == "GW3"
    assert info.imei == "123456789012345"
    assert info.status == "active"


def test_device_info_optional_fields_default():
    info = GabbDeviceInfo.from_api_response({"gabb_id": "x"})
    assert info.first_name == ""
    assert info.last_name == ""
    assert info.product_name == ""
    assert info.sku == ""
    assert info.imei is None
    assert info.status == ""


def test_device_info_imei_coerced_to_str():
    info = GabbDeviceInfo.from_api_response({"gabb_id": "x", "imei": 123456789})
    assert info.imei == "123456789"


@pytest.mark.parametrize("falsy_imei", [None, 0, "", False])
def test_device_info_imei_none_when_falsy(falsy_imei):
    info = GabbDeviceInfo.from_api_response({"gabb_id": "x", "imei": falsy_imei})
    assert info.imei is None


def test_device_info_full_name_both():
    info = GabbDeviceInfo.from_api_response(
        {"gabb_id": "x", "first_name": "Alex", "last_name": "Smith"}
    )
    assert info.full_name == "Alex Smith"


def test_device_info_full_name_first_only():
    info = GabbDeviceInfo.from_api_response({"gabb_id": "x", "first_name": "Alex"})
    assert info.full_name == "Alex"


def test_device_info_full_name_last_only():
    info = GabbDeviceInfo.from_api_response({"gabb_id": "x", "last_name": "Smith"})
    assert info.full_name == "Smith"


def test_device_info_full_name_empty():
    info = GabbDeviceInfo.from_api_response({"gabb_id": "x"})
    assert info.full_name == ""


# ---------------------------------------------------------------------------
# GabbDeviceData.from_location
# ---------------------------------------------------------------------------


def test_device_data_from_location_all_fields():
    data = {
        "gabb_id": "device-abc",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "accuracy": 10.0,
        "altitude": 5.0,
        "speed": 0.5,
        "battery_level": 85,
        "timestamp": "2024-01-01T12:00:00Z",
        "created_at": "2024-01-01T11:00:00Z",
        "device_id": "AlexDevice",
        "imei": "123456789012345",
        "shutdown": 0,
    }
    device = GabbDeviceData.from_location(data)
    assert device.gabb_id == "device-abc"
    assert device.latitude == 40.7128
    assert device.longitude == -74.0060
    assert device.accuracy == 10.0
    assert device.altitude == 5.0
    assert device.speed == 0.5
    assert device.battery_level == 85
    assert device.timestamp == "2024-01-01T12:00:00Z"
    assert device.created_at == "2024-01-01T11:00:00Z"
    assert device.first_name == "AlexDevice"  # device_id maps to first_name
    assert device.imei == "123456789012345"
    assert device.shutdown == 0
    assert device.raw_data == data


def test_device_data_from_location_missing_coords():
    device = GabbDeviceData.from_location({"gabb_id": "x"})
    assert device.latitude is None
    assert device.longitude is None


# ---------------------------------------------------------------------------
# GabbDeviceData.merge_device_info
# ---------------------------------------------------------------------------


def test_merge_device_info_overwrites_names():
    device = GabbDeviceData.from_location({"gabb_id": "x", "device_id": "OldName"})
    info = GabbDeviceInfo(
        gabb_id="x",
        first_name="Alex",
        last_name="Smith",
        product_name="Watch 3",
        sku="GW3",
        imei="999",
        status="active",
    )
    device.merge_device_info(info)
    assert device.first_name == "Alex"
    assert device.last_name == "Smith"
    assert device.product_name == "Watch 3"
    assert device.sku == "GW3"
    assert device.imei == "999"


def test_merge_device_info_keeps_existing_imei_when_info_has_none():
    device = GabbDeviceData.from_location({"gabb_id": "x", "imei": "original-imei"})
    info = GabbDeviceInfo(
        gabb_id="x",
        first_name="",
        last_name="",
        product_name="",
        sku="",
        imei=None,
        status="",
    )
    device.merge_device_info(info)
    assert device.imei == "original-imei"


# ---------------------------------------------------------------------------
# GabbDeviceData.full_name
# ---------------------------------------------------------------------------


def test_device_data_full_name_both():
    device = GabbDeviceData.from_location({"gabb_id": "abcdefgh1234"})
    device.first_name = "Alex"
    device.last_name = "Smith"
    assert device.full_name == "Alex Smith"


def test_device_data_full_name_fallback():
    device = GabbDeviceData.from_location({"gabb_id": "abcdefgh1234"})
    device.first_name = ""
    device.last_name = ""
    assert device.full_name == "Gabb Device abcdefgh"


# ---------------------------------------------------------------------------
# GabbCoordinatorData.from_api_responses
# ---------------------------------------------------------------------------


def test_coordinator_data_device_in_both(location_response, device_response):
    data = GabbCoordinatorData.from_api_responses(location_response, device_response)
    assert len(data.devices) == 1
    device = data.devices["device-abc"]
    assert device.first_name == "Alex"
    assert device.latitude == 40.7128


def test_coordinator_data_location_only():
    locations = [{"gabb_id": "loc-only", "latitude": 1.0, "longitude": 2.0}]
    data = GabbCoordinatorData.from_api_responses(locations, [])
    assert "loc-only" in data.devices
    assert data.devices["loc-only"].first_name == ""


def test_coordinator_data_device_info_only(device_response):
    data = GabbCoordinatorData.from_api_responses([], device_response)
    assert "device-abc" in data.devices
    device = data.devices["device-abc"]
    assert device.latitude is None
    assert device.first_name == "Alex"


def test_coordinator_data_empty():
    data = GabbCoordinatorData.from_api_responses([], [])
    assert data.devices == {}


def test_coordinator_data_multiple_devices():
    locations = [
        {"gabb_id": "dev-1", "latitude": 1.0},
        {"gabb_id": "dev-2", "latitude": 2.0},
    ]
    data = GabbCoordinatorData.from_api_responses(locations, [])
    assert len(data.devices) == 2
    assert "dev-1" in data.devices
    assert "dev-2" in data.devices
