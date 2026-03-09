# Gabb Home Assistant Integration

Custom Home Assistant integration for Gabb Wireless kids' smartwatch/phone monitoring. Read-only — exposes device location and battery level.

## Project Structure

```
custom_components/gabb/
├── __init__.py          # Integration setup, platform registration
├── api.py               # Async API client (aiohttp)
├── config_flow.py       # Setup UI, reauth, options flow
├── coordinator.py       # DataUpdateCoordinator (polling)
├── const.py             # Constants, API URLs, hardcoded tokens
├── models.py            # GabbDeviceInfo, GabbDeviceData, GabbCoordinatorData
├── entity.py            # GabbBaseEntity base class
├── sensor.py            # Battery sensor (%)
├── device_tracker.py    # GPS tracker (lat/lon/accuracy)
├── exceptions.py        # GabbError → GabbAuthError, GabbConnectionError, GabbAPIError
├── diagnostics.py       # Redacted diagnostics export
├── manifest.json        # Integration metadata (v0.1.0)
├── strings.json         # UI strings
├── hacs.json            # HACS metadata
└── translations/en.json # English translations
```

Supporting files at repo root:
- `docker-compose.yml` — Dev HA container (port 8123)
- `smoke_test.py` — Standalone API test script
- `gabb-python-library-reference.md` — Full FiLIP/Gabb API docs (50+ endpoints documented)

## API

### Two base URLs

| Service  | Base URL                            | Purpose            |
|----------|-------------------------------------|---------------------|
| Auth/Devices | `https://gabbid.gabbcloud.com`  | Login, device list  |
| Location | `https://location.gabbcloud.com`    | GPS coordinates     |

### Endpoints used

1. **`POST /v3/device/login/parent`** — Login with email/password. Returns `access_token`, `refresh_token`, expiration.
2. **`POST /v3/device/login/refresh`** — Refresh access token using refresh token.
3. **`GET /v3/device/account/devices/full`** — All devices with metadata (name, SKU, IMEI, status).
4. **`GET /api/location/get-all?force=true`** — All device locations (lat, lon, battery, speed, altitude, accuracy, timestamp).

### Auth headers

```python
{
    "authorization": f"Bearer {access_token}",  # CLIENT_TOKEN for login
    "api-key": LOCATION_API_KEY,
    "user-agent": "com.gabbwireless.myGabbApp/iOS/2.12.0",
    "x-accept-version": "1.0",
}
```

Hardcoded tokens in `const.py`: `CLIENT_TOKEN` (auth requests) and `LOCATION_API_KEY` (location requests).

### Error handling

- **401/403** → `GabbAuthError` → triggers reauth flow
- **Other 4xx/5xx** → `GabbAPIError`
- **Network errors** → `GabbConnectionError` → HA retries with backoff

Token refresh is automatic: on 401, refresh token is tried first, then full re-login.

## Entities

Each Gabb device creates two entities:

| Platform | Entity Class | Key Attributes |
|----------|-------------|----------------|
| `device_tracker` | `GabbDeviceTracker` | latitude, longitude, location_accuracy, altitude, speed, imei |
| `sensor` | `GabbBatterySensor` | battery percentage (0-100), device_class=BATTERY |

New devices are discovered dynamically during coordinator updates — no reload needed.

### Entity ID format
- Unique ID: `{gabb_id}_{entity_type}`
- Device identifier: `(DOMAIN, gabb_id)`

## Config Flow

1. **User step**: Enter email + password → validates via login + location fetch
2. **Options flow**: Adjust update interval (default 60s, minimum 60s)
3. **Reauth flow**: Re-enter password when token expires permanently

Unique ID per entry: lowercase email address.

## Coordinator

`GabbDataUpdateCoordinator` polls both APIs in parallel, merges results into `GabbCoordinatorData` (dict of `gabb_id` → `GabbDeviceData`). Default interval: 60 seconds.

## Testing

### Smoke test (no HA required)

```bash
python smoke_test.py
```

Prompts for Gabb credentials, calls the API directly, and prints device info (coordinates, battery, names, IMEI).

### Local Home Assistant dev environment

```bash
docker compose up
```

Starts HA on http://localhost:8123 with the integration mounted read-only. Add the Gabb integration through the HA UI.

### No automated tests yet

There are no pytest-based unit or integration tests. The smoke test is the only validation tool.

## Key Patterns

- **Async throughout**: all API calls use aiohttp via `GabbAPI`
- **Coordinator pattern**: standard HA `DataUpdateCoordinator` with parallel API fetches
- **Entity base class**: `GabbBaseEntity` provides `device_info` and data access from coordinator
- **Diagnostics**: redacts sensitive fields (tokens, coords, IMEI, IDs)
- **Domain**: `gabb` (`DOMAIN` in const.py, `MANUFACTURER = "Gabb Wireless"`)

## Limitations

- Read-only (no device control)
- Only uses 4 of 50+ available API endpoints
- No push notifications — polling only
- No automated test suite
