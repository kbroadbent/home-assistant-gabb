"""Tests for exceptions.py."""

import pytest

from custom_components.gabb.exceptions import (
    GabbAPIError,
    GabbAuthError,
    GabbConnectionError,
    GabbError,
)


def test_hierarchy():
    assert issubclass(GabbAuthError, GabbError)
    assert issubclass(GabbConnectionError, GabbError)
    assert issubclass(GabbAPIError, GabbError)
    assert issubclass(GabbError, Exception)


def test_messages_preserved():
    assert str(GabbAuthError("auth failed")) == "auth failed"
    assert str(GabbConnectionError("network error")) == "network error"
    assert str(GabbAPIError("api error 500")) == "api error 500"


def test_can_be_caught_as_gabb_error():
    with pytest.raises(GabbError):
        raise GabbAuthError("test")

    with pytest.raises(GabbError):
        raise GabbConnectionError("test")

    with pytest.raises(GabbError):
        raise GabbAPIError("test")
