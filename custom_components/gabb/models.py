"""Data models for the Gabb integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GabbDeviceInfo:
    """Static device metadata from /v3/device/account/devices/full."""

    gabb_id: str
    first_name: str
    last_name: str
    product_name: str
    sku: str
    imei: str | None
    status: str

    @staticmethod
    def from_api_response(data: dict[str, Any]) -> GabbDeviceInfo:
        return GabbDeviceInfo(
            gabb_id=data["gabb_id"],
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            product_name=data.get("productName", ""),
            sku=data.get("sku", ""),
            imei=str(data["imei"]) if data.get("imei") else None,
            status=data.get("status", ""),
        )

    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p).strip()


@dataclass
class GabbDeviceData:
    """Combined device data (location + metadata)."""

    gabb_id: str
    # Location fields
    latitude: float | None
    longitude: float | None
    accuracy: float | None
    altitude: float | None
    speed: float | None
    battery_level: int | None
    timestamp: str | None
    created_at: str | None
    # Metadata fields (from device info)
    first_name: str = ""
    last_name: str = ""
    product_name: str = ""
    sku: str = ""
    imei: str | None = None
    shutdown: int = 0
    raw_data: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_location(data: dict[str, Any]) -> GabbDeviceData:
        """Create from a location API response dict."""
        return GabbDeviceData(
            gabb_id=data["gabb_id"],
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            accuracy=data.get("accuracy"),
            altitude=data.get("altitude"),
            speed=data.get("speed"),
            battery_level=data.get("battery_level"),
            timestamp=data.get("timestamp"),
            created_at=data.get("created_at"),
            first_name=data.get("device_id", ""),  # location API uses device_id for name
            imei=data.get("imei"),
            shutdown=data.get("shutdown", 0),
            raw_data=data,
        )

    def merge_device_info(self, info: GabbDeviceInfo) -> None:
        """Merge static device metadata into this record."""
        self.first_name = info.first_name
        self.last_name = info.last_name
        self.product_name = info.product_name
        self.sku = info.sku
        if info.imei:
            self.imei = info.imei

    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p).strip() or f"Gabb Device {self.gabb_id[:8]}"


@dataclass
class GabbCoordinatorData:
    """Data returned by the coordinator."""

    devices: dict[str, GabbDeviceData] = field(default_factory=dict)

    @staticmethod
    def from_api_responses(
        locations: list[dict[str, Any]],
        device_infos: list[dict[str, Any]],
    ) -> GabbCoordinatorData:
        """Create coordinator data from location + device info responses."""
        # Build device info lookup
        info_by_id: dict[str, GabbDeviceInfo] = {}
        for item in device_infos:
            info = GabbDeviceInfo.from_api_response(item)
            info_by_id[info.gabb_id] = info

        # Build devices from location data, enriched with device info
        devices: dict[str, GabbDeviceData] = {}
        for item in locations:
            device = GabbDeviceData.from_location(item)
            if device.gabb_id in info_by_id:
                device.merge_device_info(info_by_id[device.gabb_id])
            devices[device.gabb_id] = device

        # Include devices that have metadata but no location data
        for gabb_id, info in info_by_id.items():
            if gabb_id not in devices:
                devices[gabb_id] = GabbDeviceData(
                    gabb_id=gabb_id,
                    latitude=None,
                    longitude=None,
                    accuracy=None,
                    altitude=None,
                    speed=None,
                    battery_level=None,
                    timestamp=None,
                    created_at=None,
                    first_name=info.first_name,
                    last_name=info.last_name,
                    product_name=info.product_name,
                    sku=info.sku,
                    imei=info.imei,
                )

        return GabbCoordinatorData(devices=devices)
