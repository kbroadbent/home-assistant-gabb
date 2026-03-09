"""Exceptions for the Gabb integration."""


class GabbError(Exception):
    """Base exception for Gabb."""


class GabbAuthError(GabbError):
    """Authentication error — triggers reauth."""


class GabbConnectionError(GabbError):
    """Network/connection error."""


class GabbAPIError(GabbError):
    """Unexpected API status code."""
