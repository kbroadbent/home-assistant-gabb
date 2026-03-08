"""Base entity for the Gabb integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import GabbDataUpdateCoordinator
from .models import GabbDeviceData


class GabbBaseEntity(CoordinatorEntity[GabbDataUpdateCoordinator]):
    """Base class for Gabb entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GabbDataUpdateCoordinator,
        gabb_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._gabb_id = gabb_id

    @property
    def device_data(self) -> GabbDeviceData | None:
        """Return the device data from the coordinator."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.devices.get(self._gabb_id)

    @property
    def available(self) -> bool:
        """Return True if the device is available."""
        return super().available and self.device_data is not None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this Gabb device."""
        device = self.device_data
        name = device.full_name if device else f"Gabb Device {self._gabb_id[:8]}"
        return DeviceInfo(
            identifiers={(DOMAIN, self._gabb_id)},
            name=name,
            manufacturer=MANUFACTURER,
            model=device.product_name if device and device.product_name else None,
        )
