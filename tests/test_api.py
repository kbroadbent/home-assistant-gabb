"""Tests for api.py."""

import pytest
import aiohttp
from aioresponses import aioresponses

from custom_components.gabb.api import GabbAPI
from custom_components.gabb.const import AUTH_BASE_URL, LOCATION_BASE_URL
from custom_components.gabb.exceptions import GabbAPIError, GabbAuthError, GabbConnectionError


def make_api(session, username="u@example.com", password="pass"):
    return GabbAPI(session, username, password)


# ---------------------------------------------------------------------------
# login()
# ---------------------------------------------------------------------------


async def test_login_success(login_response):
    async with aiohttp.ClientSession() as session:
        api = make_api(session)
        with aioresponses() as m:
            m.post(f"{AUTH_BASE_URL}/v3/device/login/parent", payload=login_response)
            await api.login()
    assert api._access_token == "test-access-token"
    assert api._refresh_token == "test-refresh-token"


async def test_login_stores_tokens(login_response):
    async with aiohttp.ClientSession() as session:
        api = make_api(session)
        with aioresponses() as m:
            m.post(f"{AUTH_BASE_URL}/v3/device/login/parent", payload=login_response)
            result = await api.login()
    assert result["access_token"] == "test-access-token"


async def test_login_401_raises_auth_error():
    async with aiohttp.ClientSession() as session:
        api = make_api(session)
        with aioresponses() as m:
            m.post(f"{AUTH_BASE_URL}/v3/device/login/parent", status=401)
            with pytest.raises(GabbAuthError):
                await api.login()


async def test_login_403_raises_auth_error():
    async with aiohttp.ClientSession() as session:
        api = make_api(session)
        with aioresponses() as m:
            m.post(f"{AUTH_BASE_URL}/v3/device/login/parent", status=403)
            with pytest.raises(GabbAuthError):
                await api.login()


async def test_login_500_raises_api_error():
    async with aiohttp.ClientSession() as session:
        api = make_api(session)
        with aioresponses() as m:
            m.post(
                f"{AUTH_BASE_URL}/v3/device/login/parent",
                status=500,
                body=b"Internal Server Error",
            )
            with pytest.raises(GabbAPIError):
                await api.login()


async def test_login_client_error_raises_connection_error():
    async with aiohttp.ClientSession() as session:
        api = make_api(session)
        with aioresponses() as m:
            m.post(
                f"{AUTH_BASE_URL}/v3/device/login/parent",
                exception=aiohttp.ClientConnectionError("conn refused"),
            )
            with pytest.raises(GabbConnectionError):
                await api.login()


# ---------------------------------------------------------------------------
# refresh_access_token()
# ---------------------------------------------------------------------------


async def test_refresh_success():
    async with aiohttp.ClientSession() as session:
        api = make_api(session)
        api._refresh_token = "old-refresh-token"
        api._access_token = "old-access-token"
        with aioresponses() as m:
            m.post(
                f"{AUTH_BASE_URL}/v3/device/login/refresh",
                payload={"access_token": "new-access-token"},
            )
            await api.refresh_access_token()
    assert api._access_token == "new-access-token"


async def test_refresh_no_refresh_token_calls_login(login_response):
    async with aiohttp.ClientSession() as session:
        api = make_api(session)
        api._refresh_token = None
        with aioresponses() as m:
            m.post(f"{AUTH_BASE_URL}/v3/device/login/parent", payload=login_response)
            await api.refresh_access_token()
    assert api._access_token == "test-access-token"


async def test_refresh_401_falls_back_to_login(login_response):
    async with aiohttp.ClientSession() as session:
        api = make_api(session)
        api._refresh_token = "stale-refresh-token"
        with aioresponses() as m:
            m.post(f"{AUTH_BASE_URL}/v3/device/login/refresh", status=401)
            m.post(f"{AUTH_BASE_URL}/v3/device/login/parent", payload=login_response)
            await api.refresh_access_token()
    assert api._access_token == "test-access-token"


async def test_refresh_client_error_falls_back_to_login(login_response):
    async with aiohttp.ClientSession() as session:
        api = make_api(session)
        api._refresh_token = "some-refresh-token"
        with aioresponses() as m:
            m.post(
                f"{AUTH_BASE_URL}/v3/device/login/refresh",
                exception=aiohttp.ClientConnectionError("err"),
            )
            m.post(f"{AUTH_BASE_URL}/v3/device/login/parent", payload=login_response)
            await api.refresh_access_token()
    assert api._access_token == "test-access-token"


async def test_refresh_preserves_token_when_response_lacks_access_token():
    async with aiohttp.ClientSession() as session:
        api = make_api(session)
        api._refresh_token = "refresh-tok"
        api._access_token = "existing-token"
        with aioresponses() as m:
            m.post(
                f"{AUTH_BASE_URL}/v3/device/login/refresh",
                payload={},  # no access_token key
            )
            await api.refresh_access_token()
    assert api._access_token == "existing-token"


# ---------------------------------------------------------------------------
# get_devices()
# ---------------------------------------------------------------------------


async def test_get_devices_success(device_response):
    async with aiohttp.ClientSession() as session:
        api = make_api(session)
        api._access_token = "tok"
        with aioresponses() as m:
            m.get(
                f"{AUTH_BASE_URL}/v3/device/account/devices/full",
                payload={"lines": device_response},
            )
            result = await api.get_devices()
    assert result == device_response


async def test_get_devices_missing_lines_key():
    async with aiohttp.ClientSession() as session:
        api = make_api(session)
        api._access_token = "tok"
        with aioresponses() as m:
            m.get(
                f"{AUTH_BASE_URL}/v3/device/account/devices/full",
                payload={"other_key": []},
            )
            result = await api.get_devices()
    assert result == []


async def test_get_devices_401_raises_auth_error():
    async with aiohttp.ClientSession() as session:
        api = make_api(session)
        api._access_token = "tok"
        with aioresponses() as m:
            m.get(f"{AUTH_BASE_URL}/v3/device/account/devices/full", status=401)
            with pytest.raises(GabbAuthError):
                await api.get_devices()


async def test_get_devices_client_error_raises_connection_error():
    async with aiohttp.ClientSession() as session:
        api = make_api(session)
        api._access_token = "tok"
        with aioresponses() as m:
            m.get(
                f"{AUTH_BASE_URL}/v3/device/account/devices/full",
                exception=aiohttp.ClientConnectionError("err"),
            )
            with pytest.raises(GabbConnectionError):
                await api.get_devices()


# ---------------------------------------------------------------------------
# get_locations()
# ---------------------------------------------------------------------------


async def test_get_locations_success(location_response):
    async with aiohttp.ClientSession() as session:
        api = make_api(session)
        api._access_token = "tok"
        with aioresponses() as m:
            m.get(
                f"{LOCATION_BASE_URL}/api/location/get-all?force=true",
                payload=location_response,
            )
            result = await api.get_locations()
    assert result == location_response


async def test_get_locations_401_raises_auth_error():
    async with aiohttp.ClientSession() as session:
        api = make_api(session)
        api._access_token = "tok"
        with aioresponses() as m:
            m.get(f"{LOCATION_BASE_URL}/api/location/get-all?force=true", status=401)
            with pytest.raises(GabbAuthError):
                await api.get_locations()


async def test_get_locations_403_raises_auth_error():
    async with aiohttp.ClientSession() as session:
        api = make_api(session)
        api._access_token = "tok"
        with aioresponses() as m:
            m.get(f"{LOCATION_BASE_URL}/api/location/get-all?force=true", status=403)
            with pytest.raises(GabbAuthError):
                await api.get_locations()


async def test_get_locations_500_raises_api_error():
    async with aiohttp.ClientSession() as session:
        api = make_api(session)
        api._access_token = "tok"
        with aioresponses() as m:
            m.get(
                f"{LOCATION_BASE_URL}/api/location/get-all?force=true",
                status=500,
                body=b"Server Error",
            )
            with pytest.raises(GabbAPIError):
                await api.get_locations()


async def test_get_locations_client_error_raises_connection_error():
    async with aiohttp.ClientSession() as session:
        api = make_api(session)
        api._access_token = "tok"
        with aioresponses() as m:
            m.get(
                f"{LOCATION_BASE_URL}/api/location/get-all?force=true",
                exception=aiohttp.ClientConnectionError("err"),
            )
            with pytest.raises(GabbConnectionError):
                await api.get_locations()


# ---------------------------------------------------------------------------
# close()
# ---------------------------------------------------------------------------


async def test_close():
    session = aiohttp.ClientSession()
    api = make_api(session)
    await api.close()
    assert session.closed
