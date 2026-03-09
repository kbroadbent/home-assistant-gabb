"""Sensor platform for Gabb."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import GabbDataUpdateCoordinator
from .entity import GabbBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Gabb sensor entities."""
    coordinator: GabbDataUpdateCoordinator = entry.runtime_data
    known_ids: set[str] = set(coordinator.data.devices)
    async_add_entities(
        GabbBatterySensor(coordinator, gabb_id)
        for gabb_id in known_ids
    )

    @callback
    def _async_add_new_devices() -> None:
        """Add entities for any newly discovered devices."""
        if coordinator.data is None:
            return
        new_ids = set(coordinator.data.devices) - known_ids
        if new_ids:
            known_ids.update(new_ids)
            async_add_entities(
                GabbBatterySensor(coordinator, gabb_id)
                for gabb_id in new_ids
            )

    entry.async_on_unload(coordinator.async_add_listener(_async_add_new_devices))


class GabbBatterySensor(GabbBaseEntity, SensorEntity):
    """Battery level sensor for a Gabb device."""

    _attr_name = "Battery"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: GabbDataUpdateCoordinator,
        gabb_id: str,
    ) -> None:
        super().__init__(coordinator, gabb_id)
        self._attr_unique_id = f"{gabb_id}_battery"

    @property
    def native_value(self) -> int | None:
        """Return the battery level."""
        device = self.device_data
        return device.battery_level if device else None
