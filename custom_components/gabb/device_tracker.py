"""Device tracker platform for Gabb."""

from __future__ import annotations

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import GabbDataUpdateCoordinator
from .entity import GabbBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Gabb device tracker entities."""
    coordinator: GabbDataUpdateCoordinator = entry.runtime_data
    known_ids: set[str] = set(coordinator.data.devices)
    async_add_entities(
        GabbDeviceTracker(coordinator, gabb_id)
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
                GabbDeviceTracker(coordinator, gabb_id)
                for gabb_id in new_ids
            )

    entry.async_on_unload(coordinator.async_add_listener(_async_add_new_devices))


class GabbDeviceTracker(GabbBaseEntity, TrackerEntity):
    """Gabb GPS device tracker."""

    _attr_name = None  # Use device name directly
    _attr_entity_category = None

    def __init__(
        self,
        coordinator: GabbDataUpdateCoordinator,
        gabb_id: str,
    ) -> None:
        super().__init__(coordinator, gabb_id)
        self._attr_unique_id = f"{gabb_id}_tracker"

    @property
    def source_type(self) -> SourceType:
        """Return the source type."""
        return SourceType.GPS

    @property
    def latitude(self) -> float | None:
        """Return latitude."""
        device = self.device_data
        return device.latitude if device else None

    @property
    def longitude(self) -> float | None:
        """Return longitude."""
        device = self.device_data
        return device.longitude if device else None

    @property
    def location_accuracy(self) -> int:
        """Return the GPS accuracy in meters."""
        device = self.device_data
        if device and device.accuracy is not None:
            return int(device.accuracy)
        return 0

    @property
    def extra_state_attributes(self) -> dict[str, str | int | float | None]:
        """Return extra state attributes."""
        device = self.device_data
        if device is None:
            return {}
        return {
            "altitude": device.altitude,
            "speed": device.speed,
            "imei": device.imei,
        }
