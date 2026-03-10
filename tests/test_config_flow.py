"""Tests for config_flow.py."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.gabb.config_flow import (
    GabbConfigFlow,
    GabbOptionsFlow,
    _validate_credentials,
)
from custom_components.gabb.const import CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
from custom_components.gabb.exceptions import GabbAuthError, GabbConnectionError
from homeassistant.config_entries import ConfigEntry


# ---------------------------------------------------------------------------
# _validate_credentials
# ---------------------------------------------------------------------------


async def test_validate_credentials_success():
    with patch("custom_components.gabb.config_flow.GabbAPI") as mock_cls:
        mock_api = AsyncMock()
        mock_cls.return_value = mock_api
        with patch("aiohttp.ClientSession") as mock_session_cls:
            mock_session_cls.return_value = AsyncMock()
            await _validate_credentials("user@example.com", "pass")
    mock_api.login.assert_called_once()
    mock_api.get_locations.assert_called_once()


async def test_validate_credentials_propagates_auth_error():
    with patch("custom_components.gabb.config_flow.GabbAPI") as mock_cls:
        mock_api = AsyncMock()
        mock_api.login.side_effect = GabbAuthError("bad creds")
        mock_cls.return_value = mock_api
        with patch("aiohttp.ClientSession") as mock_session_cls:
            mock_session_cls.return_value = AsyncMock()
            with pytest.raises(GabbAuthError):
                await _validate_credentials("u@example.com", "wrong")


async def test_validate_credentials_propagates_connection_error():
    with patch("custom_components.gabb.config_flow.GabbAPI") as mock_cls:
        mock_api = AsyncMock()
        mock_api.login.side_effect = GabbConnectionError("offline")
        mock_cls.return_value = mock_api
        with patch("aiohttp.ClientSession") as mock_session_cls:
            mock_session_cls.return_value = AsyncMock()
            with pytest.raises(GabbConnectionError):
                await _validate_credentials("u@example.com", "pass")


async def test_validate_credentials_session_closed_on_exception():
    mock_session = AsyncMock()
    with patch("custom_components.gabb.config_flow.GabbAPI") as mock_cls:
        mock_api = AsyncMock()
        mock_api.login.side_effect = GabbConnectionError("offline")
        mock_cls.return_value = mock_api
        with patch("aiohttp.ClientSession") as mock_session_cls:
            mock_session_cls.return_value = mock_session
            with pytest.raises(GabbConnectionError):
                await _validate_credentials("u@example.com", "pass")
    mock_session.close.assert_called_once()


# ---------------------------------------------------------------------------
# GabbConfigFlow.async_step_user
# ---------------------------------------------------------------------------


async def test_step_user_none_input_shows_form():
    flow = GabbConfigFlow()
    result = await flow.async_step_user(None)
    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_step_user_valid_input_creates_entry():
    flow = GabbConfigFlow()
    with patch(
        "custom_components.gabb.config_flow._validate_credentials",
        new_callable=AsyncMock,
    ):
        result = await flow.async_step_user(
            {"username": "User@Example.com", "password": "secret"}
        )
    assert result["type"] == "create_entry"
    assert result["data"]["username"] == "user@example.com"  # lowercased


async def test_step_user_auth_error_shows_form():
    flow = GabbConfigFlow()
    with patch(
        "custom_components.gabb.config_flow._validate_credentials",
        new_callable=AsyncMock,
        side_effect=GabbAuthError("bad"),
    ):
        result = await flow.async_step_user(
            {"username": "u@example.com", "password": "wrong"}
        )
    assert result["type"] == "form"
    assert result["errors"]["base"] == "invalid_auth"


async def test_step_user_connection_error_shows_form():
    flow = GabbConfigFlow()
    with patch(
        "custom_components.gabb.config_flow._validate_credentials",
        new_callable=AsyncMock,
        side_effect=GabbConnectionError("offline"),
    ):
        result = await flow.async_step_user(
            {"username": "u@example.com", "password": "pass"}
        )
    assert result["type"] == "form"
    assert result["errors"]["base"] == "cannot_connect"


async def test_step_user_unexpected_error_shows_form():
    flow = GabbConfigFlow()
    with patch(
        "custom_components.gabb.config_flow._validate_credentials",
        new_callable=AsyncMock,
        side_effect=RuntimeError("boom"),
    ):
        result = await flow.async_step_user(
            {"username": "u@example.com", "password": "pass"}
        )
    assert result["type"] == "form"
    assert result["errors"]["base"] == "unknown"


# ---------------------------------------------------------------------------
# GabbConfigFlow.async_step_reauth_confirm
# ---------------------------------------------------------------------------


async def test_step_reauth_confirm_none_input_shows_form():
    flow = GabbConfigFlow()
    flow._reauth_entry_data = {"username": "u@example.com", "password": "old"}
    result = await flow.async_step_reauth_confirm(None)
    assert result["type"] == "form"
    assert result["step_id"] == "reauth_confirm"


async def test_step_reauth_confirm_valid_aborts_with_success():
    flow = GabbConfigFlow()
    flow._reauth_entry_data = {"username": "u@example.com", "password": "old"}
    flow.context = {"entry_id": "entry-123"}

    mock_entry = MagicMock()
    mock_entry.entry_id = "entry-123"
    flow.hass.config_entries.async_get_entry.return_value = mock_entry
    flow.hass.config_entries.async_reload = AsyncMock()

    with patch(
        "custom_components.gabb.config_flow._validate_credentials",
        new_callable=AsyncMock,
    ):
        result = await flow.async_step_reauth_confirm({"password": "new-pass"})

    assert result["type"] == "abort"
    assert result["reason"] == "reauth_successful"


async def test_step_reauth_confirm_auth_error_shows_form():
    flow = GabbConfigFlow()
    flow._reauth_entry_data = {"username": "u@example.com", "password": "old"}
    with patch(
        "custom_components.gabb.config_flow._validate_credentials",
        new_callable=AsyncMock,
        side_effect=GabbAuthError("bad"),
    ):
        result = await flow.async_step_reauth_confirm({"password": "wrong"})
    assert result["type"] == "form"
    assert result["errors"]["base"] == "invalid_auth"


async def test_step_reauth_confirm_connection_error_shows_form():
    flow = GabbConfigFlow()
    flow._reauth_entry_data = {"username": "u@example.com", "password": "old"}
    with patch(
        "custom_components.gabb.config_flow._validate_credentials",
        new_callable=AsyncMock,
        side_effect=GabbConnectionError("offline"),
    ):
        result = await flow.async_step_reauth_confirm({"password": "pass"})
    assert result["type"] == "form"
    assert result["errors"]["base"] == "cannot_connect"


# ---------------------------------------------------------------------------
# GabbOptionsFlow.async_step_init
# ---------------------------------------------------------------------------


async def test_options_step_init_none_input_shows_form():
    entry = ConfigEntry(options={CONF_UPDATE_INTERVAL: 120})
    flow = GabbOptionsFlow(entry)
    result = await flow.async_step_init(None)
    assert result["type"] == "form"
    assert result["step_id"] == "init"


async def test_options_step_init_valid_input_creates_entry():
    entry = ConfigEntry(options={})
    flow = GabbOptionsFlow(entry)
    result = await flow.async_step_init({CONF_UPDATE_INTERVAL: 180})
    assert result["type"] == "create_entry"
    assert result["data"] == {CONF_UPDATE_INTERVAL: 180}


async def test_options_step_init_default_interval_when_not_set():
    entry = ConfigEntry(options={})
    flow = GabbOptionsFlow(entry)
    result = await flow.async_step_init(None)
    assert result["type"] == "form"
