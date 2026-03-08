"""Async API client for the Gabb Cloud API."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import AUTH_BASE_URL, CLIENT_TOKEN, LOCATION_API_KEY, LOCATION_BASE_URL
from .exceptions import GabbAPIError, GabbAuthError, GabbConnectionError

_LOGGER = logging.getLogger(__name__)


class GabbAPI:
    """Async client for the Gabb Cloud API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
    ) -> None:
        self._session = session
        self._username = username
        self._password = password
        self._access_token: str | None = None
        self._refresh_token: str | None = None

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    async def login(self) -> dict[str, Any]:
        """Authenticate with username/password. Returns account data."""
        url = f"{AUTH_BASE_URL}/v3/device/login/parent"
        headers = {
            "authorization": f"Bearer {CLIENT_TOKEN}",
            "content-type": "application/json",
            "accept": "application/json",
        }
        payload = {
            "email": self._username,
            "password": self._password,
            "username": self._username,
        }
        try:
            async with self._session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                data = await self._handle_response(resp)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise GabbConnectionError(f"Connection error: {err}") from err

        self._access_token = data["access_token"]
        self._refresh_token = data.get("refresh_token")
        return data

    async def refresh_access_token(self) -> None:
        """Refresh the access token using the refresh token."""
        if not self._refresh_token:
            await self.login()
            return

        url = f"{AUTH_BASE_URL}/v3/device/login/refresh"
        headers = {
            "authorization": f"Bearer {CLIENT_TOKEN}",
            "content-type": "application/json",
            "accept": "application/json",
        }
        payload = {"refresh_token": self._refresh_token}
        try:
            async with self._session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status == 401:
                    await self.login()
                    return
                data = await self._handle_response(resp)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise GabbConnectionError(f"Connection error: {err}") from err

        self._access_token = data.get("access_token", self._access_token)
        self._refresh_token = data.get("refresh_token", self._refresh_token)

    # ------------------------------------------------------------------
    # Device & Location APIs
    # ------------------------------------------------------------------

    async def get_devices(self) -> list[dict[str, Any]]:
        """GET /v3/device/account/devices/full — returns device metadata."""
        url = f"{AUTH_BASE_URL}/v3/device/account/devices/full"
        headers = self._authenticated_headers()
        try:
            async with self._session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                data = await self._handle_response(resp)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise GabbConnectionError(f"Connection error: {err}") from err
        return data.get("lines", [])

    async def get_locations(self) -> list[dict[str, Any]]:
        """GET /api/location/get-all — returns all device locations."""
        url = f"{LOCATION_BASE_URL}/api/location/get-all?force=true"
        headers = self._authenticated_headers()
        try:
            async with self._session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                return await self._handle_response(resp)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise GabbConnectionError(f"Connection error: {err}") from err

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _authenticated_headers(self) -> dict[str, str]:
        return {
            "authorization": f"Bearer {self._access_token}",
            "api-key": LOCATION_API_KEY,
            "accept": "application/json",
            "content-type": "application/json",
            "user-agent": "com.gabbwireless.myGabbApp/iOS/2.12.0",
            "x-accept-version": "1.0",
        }

    # ------------------------------------------------------------------
    # Response handling
    # ------------------------------------------------------------------

    @staticmethod
    async def _handle_response(resp: aiohttp.ClientResponse) -> Any:
        if resp.status == 401:
            raise GabbAuthError("Authentication failed (401)")
        if resp.status == 403:
            raise GabbAuthError("Forbidden (403)")
        if resp.status >= 400:
            text = await resp.text()
            raise GabbAPIError(f"API error {resp.status}: {text}")
        return await resp.json()

    async def close(self) -> None:
        """Close the underlying session."""
        await self._session.close()
