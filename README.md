# Gabb Home Assistant Integration

A Home Assistant custom integration for monitoring [Gabb](https://www.gabb.com/) children's devices (watches and phones).

> **Disclaimer:** This is an unofficial integration and is not affiliated with or endorsed by Gabb Wireless. It relies on undocumented, private APIs that may change at any time without notice. Use at your own risk — interacting directly with these APIs may produce unexpected results.

## Features

- **GPS Device Tracking**: Track device locations in real-time with accuracy, altitude, and speed attributes
- **Battery Monitoring**: Monitor battery levels for all devices
- **Auto-Discovery**: Automatically discovers all devices on your Gabb account
- **Configurable Polling**: Adjustable update interval (minimum 60 seconds)
- **Reauthentication Flow**: Automatic prompt when credentials expire
- **Diagnostics Support**: Built-in diagnostics with automatic sensitive data redaction

## Installation

### HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed
2. Search for "Gabb" in the HACS Integrations store
3. Click "Download"
4. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/gabb` folder to your Home Assistant `custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings > Devices & Services
2. Click "+ Add Integration"
3. Search for "Gabb"
4. Enter your Gabb account email and password

### Options

After setup, you can configure:
- **Update Interval**: How often to poll the Gabb API (minimum 60 seconds, default: 60)

Access via: Devices & Services > Gabb > Configure

## Entities

### Device Tracker
Each Gabb device gets a GPS tracker entity with:
- Latitude / Longitude
- Location accuracy
- Altitude and speed (as extra attributes)
- IMEI (as extra attribute)

### Battery Sensor
Each Gabb device gets a battery level sensor (percentage).

---

## Development

### Local Home Assistant

```bash
# Start Home Assistant with the integration mounted
docker compose up

# Open http://localhost:8123
```

### Smoke Test (no HA required)

```bash
python smoke_test.py
```

Prompts for Gabb credentials, calls the API directly, and prints device info (coordinates, battery, names, IMEI). Useful for verifying credentials and API connectivity without a full HA setup.

### Tests

```bash
pip install -r requirements-test.txt
pytest
```

Run with coverage:

```bash
pip install pytest-cov
pytest --cov=custom_components/gabb --cov-report=term-missing
```

### Project Structure

```
home-assistant-gabb/
├── custom_components/gabb/
│   ├── __init__.py          # Integration setup, platform registration
│   ├── api.py               # Async API client (aiohttp)
│   ├── config_flow.py       # Setup UI, reauth, and options flow
│   ├── coordinator.py       # DataUpdateCoordinator (polling)
│   ├── const.py             # Constants, API URLs, hardcoded tokens
│   ├── models.py            # GabbDeviceInfo, GabbDeviceData, GabbCoordinatorData
│   ├── entity.py            # GabbBaseEntity base class
│   ├── sensor.py            # Battery sensor (%)
│   ├── device_tracker.py    # GPS tracker (lat/lon/accuracy)
│   ├── exceptions.py        # GabbError → GabbAuthError, GabbConnectionError, GabbAPIError
│   ├── diagnostics.py       # Redacted diagnostics export
│   ├── manifest.json        # Integration metadata
│   ├── strings.json         # UI strings
│   └── translations/en.json # English translations
├── tests/                   # pytest test suite
├── brand/                   # Integration icon
├── .github/workflows/       # CI/CD (HACS validation, hassfest)
├── docker-compose.yml       # Dev HA container (port 8123)
├── requirements-test.txt    # Test dependencies
└── smoke_test.py            # Standalone API test script
```

---

## Support

For issues and feature requests, use the [GitHub issue tracker](https://github.com/kbroadbent/home-assistant-gabb/issues).

## License

This integration is provided as-is for personal use.
