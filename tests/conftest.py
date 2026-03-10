"""Configure pytest with HA stubs and shared fixtures."""
from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Stub classes for homeassistant modules
# ---------------------------------------------------------------------------


class _UpdateFailed(Exception):
    """Stub for UpdateFailed."""


class _ConfigEntryAuthFailed(Exception):
    """Stub for ConfigEntryAuthFailed."""


class _DataUpdateCoordinator:
    """Minimal stub for DataUpdateCoordinator."""

    def __init__(self, hass, logger=None, config_entry=None, name=None, update_interval=None, **kwargs):
        self.hass = hass
        self.config_entry = config_entry
        self.name = name
        self.update_interval = update_interval
        self.data = None
        self.available = True
        self._listeners: list = []

    def __class_getitem__(cls, item):
        return cls

    def async_add_listener(self, listener, context=None):
        self._listeners.append(listener)
        return lambda: (self._listeners.remove(listener) if listener in self._listeners else None)


class _CoordinatorEntity:
    """Minimal stub for CoordinatorEntity."""

    def __init__(self, coordinator):
        super().__init__()
        self.coordinator = coordinator

    def __class_getitem__(cls, item):
        return cls

    @property
    def available(self) -> bool:
        return getattr(self.coordinator, "available", True)


class _ConfigFlow:
    """Minimal stub for ConfigFlow."""

    def __init_subclass__(cls, domain=None, **kwargs):
        super().__init_subclass__(**kwargs)

    def __init__(self):
        self.context: dict = {}
        self.hass = MagicMock()

    async def async_set_unique_id(self, unique_id: str) -> None:
        pass

    def _abort_if_unique_id_configured(self) -> None:
        pass

    def async_show_form(self, *, step_id, data_schema=None, errors=None, description_placeholders=None):
        return {
            "type": "form",
            "step_id": step_id,
            "data_schema": data_schema,
            "errors": errors or {},
        }

    def async_create_entry(self, *, title="", data=None, **kwargs):
        return {"type": "create_entry", "title": title, "data": data or {}}

    def async_abort(self, *, reason: str):
        return {"type": "abort", "reason": reason}


class _OptionsFlowWithConfigEntry:
    """Minimal stub for OptionsFlowWithConfigEntry."""

    def __init__(self, config_entry):
        self.config_entry = config_entry
        self.options = getattr(config_entry, "options", {})

    def async_show_form(self, *, step_id, data_schema=None, errors=None, **kwargs):
        return {
            "type": "form",
            "step_id": step_id,
            "data_schema": data_schema,
            "errors": errors or {},
        }

    def async_create_entry(self, *, title="", data=None, **kwargs):
        return {"type": "create_entry", "title": title, "data": data or {}}


class _ConfigEntry:
    """Minimal stub for ConfigEntry."""

    def __init__(self, data=None, options=None, entry_id="test-entry-id"):
        self.data = data or {}
        self.options = options or {}
        self.entry_id = entry_id
        self.runtime_data = None

    def __class_getitem__(cls, item):
        return cls

    def async_on_unload(self, func):
        pass

    def as_dict(self):
        return {
            "entry_id": self.entry_id,
            "data": self.data,
            "options": self.options,
        }


class _DeviceInfo:
    """Minimal stub for DeviceInfo."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class _SensorDeviceClass:
    BATTERY = "battery"


class _SensorStateClass:
    MEASUREMENT = "measurement"


class _SensorEntity:
    def __init__(self):
        super().__init__()


class _SourceType:
    GPS = "gps"


class _TrackerEntity:
    def __init__(self):
        super().__init__()


class _Platform:
    DEVICE_TRACKER = "device_tracker"
    SENSOR = "sensor"


def _async_redact_data(data, to_redact):
    """Real recursive redaction implementation."""
    if isinstance(data, list):
        return [_async_redact_data(v, to_redact) for v in data]
    if not isinstance(data, dict):
        return data
    result = {}
    for key, value in data.items():
        if key in to_redact:
            result[key] = "**REDACTED**"
        elif isinstance(value, (dict, list)):
            result[key] = _async_redact_data(value, to_redact)
        else:
            result[key] = value
    return result


def _callback(func):
    """Identity decorator stub for @callback."""
    return func


# ---------------------------------------------------------------------------
# Patch sys.modules before any integration code is imported
# ---------------------------------------------------------------------------


def _make_module(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


_HA_MODULES = {
    "homeassistant": _make_module("homeassistant"),
    "homeassistant.helpers": _make_module("homeassistant.helpers"),
    "homeassistant.helpers.update_coordinator": _make_module(
        "homeassistant.helpers.update_coordinator",
        DataUpdateCoordinator=_DataUpdateCoordinator,
        CoordinatorEntity=_CoordinatorEntity,
        UpdateFailed=_UpdateFailed,
    ),
    "homeassistant.config_entries": _make_module(
        "homeassistant.config_entries",
        ConfigFlow=_ConfigFlow,
        OptionsFlow=object,
        OptionsFlowWithConfigEntry=_OptionsFlowWithConfigEntry,
        ConfigEntry=_ConfigEntry,
        ConfigFlowResult=dict,
    ),
    "homeassistant.exceptions": _make_module(
        "homeassistant.exceptions",
        ConfigEntryAuthFailed=_ConfigEntryAuthFailed,
    ),
    "homeassistant.const": _make_module(
        "homeassistant.const",
        CONF_PASSWORD="password",
        CONF_USERNAME="username",
        PERCENTAGE="%",
        Platform=_Platform,
    ),
    "homeassistant.core": _make_module(
        "homeassistant.core",
        HomeAssistant=MagicMock,
        callback=_callback,
    ),
    "homeassistant.helpers.device_registry": _make_module(
        "homeassistant.helpers.device_registry",
        DeviceInfo=_DeviceInfo,
    ),
    "homeassistant.helpers.entity_platform": _make_module(
        "homeassistant.helpers.entity_platform",
        AddEntitiesCallback=None,
    ),
    "homeassistant.components": _make_module("homeassistant.components"),
    "homeassistant.components.sensor": _make_module(
        "homeassistant.components.sensor",
        SensorDeviceClass=_SensorDeviceClass,
        SensorStateClass=_SensorStateClass,
        SensorEntity=_SensorEntity,
    ),
    "homeassistant.components.device_tracker": _make_module(
        "homeassistant.components.device_tracker",
        SourceType=_SourceType,
        TrackerEntity=_TrackerEntity,
    ),
    "homeassistant.components.diagnostics": _make_module(
        "homeassistant.components.diagnostics",
        async_redact_data=_async_redact_data,
    ),
}

for _name, _mod in _HA_MODULES.items():
    sys.modules[_name] = _mod


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def login_response():
    return {
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
        "account": {"id": "acct-123"},
    }


@pytest.fixture
def location_response():
    return [
        {
            "gabb_id": "device-abc",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "accuracy": 10.0,
            "altitude": 5.0,
            "speed": 0.0,
            "battery_level": 85,
            "timestamp": "2024-01-01T12:00:00Z",
            "created_at": "2024-01-01T12:00:00Z",
            "imei": "123456789012345",
            "shutdown": 0,
        }
    ]


@pytest.fixture
def device_response():
    return [
        {
            "gabb_id": "device-abc",
            "first_name": "Alex",
            "last_name": "Smith",
            "productName": "Gabb Watch 3",
            "sku": "GW3",
            "imei": "123456789012345",
            "status": "active",
        }
    ]


@pytest.fixture
def coordinator_data(location_response, device_response):
    from custom_components.gabb.models import GabbCoordinatorData

    return GabbCoordinatorData.from_api_responses(location_response, device_response)


@pytest.fixture
def mock_coordinator(coordinator_data):
    coord = MagicMock()
    coord.data = coordinator_data
    coord.available = True
    coord._listeners = []

    def _add_listener(listener, context=None):
        coord._listeners.append(listener)
        return lambda: None

    coord.async_add_listener = _add_listener
    return coord


@pytest.fixture
def config_entry():
    return _ConfigEntry(
        data={"username": "user@example.com", "password": "secret"},
        options={},
    )
