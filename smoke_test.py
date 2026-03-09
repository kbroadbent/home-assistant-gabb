"""Smoke test for the Gabb Cloud API.

Usage:
    python smoke_test.py
"""

import asyncio
import getpass
import json
import sys

import aiohttp

sys.path.insert(0, ".")
from custom_components.gabb.api import GabbAPI
from custom_components.gabb.models import GabbCoordinatorData


async def main() -> None:
    email = input("Gabb email: ").strip()
    password = getpass.getpass("Gabb password: ")

    session = aiohttp.ClientSession()
    api = GabbAPI(session, email, password)

    try:
        print("\n--- Logging in...")
        account_data = await api.login()
        account = account_data.get("account", {})
        print(f"Login successful. Welcome {account.get('first_name', '')}!")
        print(f"Children: {account.get('total_children', 0)}")

        print("\n--- Fetching device info...")
        devices = await api.get_devices()
        print(json.dumps(devices, indent=2, default=str))

        print("\n--- Fetching locations...")
        locations = await api.get_locations()
        print(json.dumps(locations, indent=2, default=str))

        print("\n--- Parsing into models...")
        coordinator_data = GabbCoordinatorData.from_api_responses(locations, devices)

        print(f"\nFound {len(coordinator_data.devices)} device(s):\n")
        for gabb_id, device in coordinator_data.devices.items():
            print(f"  Gabb ID:    {gabb_id}")
            print(f"  Name:       {device.full_name}")
            print(f"  Product:    {device.product_name}")
            print(f"  Latitude:   {device.latitude}")
            print(f"  Longitude:  {device.longitude}")
            print(f"  Accuracy:   {device.accuracy}m")
            print(f"  Battery:    {device.battery_level}%")
            print(f"  IMEI:       {device.imei}")
            print(f"  Updated:    {device.created_at}")
            print()

        if not coordinator_data.devices:
            print("  (no devices found)")

    except Exception as e:
        print(f"\nError: {type(e).__name__}: {e}")
        raise
    finally:
        await session.close()


if __name__ == "__main__":
    asyncio.run(main())
