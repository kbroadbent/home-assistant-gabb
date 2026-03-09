# Gabb Home Assistant Integration

A Home Assistant custom integration for monitoring [Gabb](https://www.gabb.com/) children's devices (watches and phones).

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

## Support

For issues and feature requests, use the [GitHub issue tracker](https://github.com/kbroadbent/home-assistant-gabb/issues).

## License

This integration is provided as-is for personal use.
