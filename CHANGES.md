# Changelog

## 0.1.0

Initial release.

- GPS device tracking (latitude, longitude, accuracy, altitude, speed) for all Gabb devices
- Battery level sensor for all Gabb devices
- Automatic device discovery — all devices on the account are found without manual configuration
- Config flow UI for email/password setup
- Reauthentication flow when credentials expire
- Options flow to configure update interval (default: 60 seconds)
- Automatic token refresh — uses refresh token on 401 before prompting for reauth
- Diagnostics support with automatic redaction of sensitive fields (tokens, coordinates, IMEI, IDs)
- New devices are picked up dynamically during coordinator updates without requiring a reload
