# Gabb Wireless Python Library - Complete API Reference

**Source**: https://github.com/woodsbw/gabb/tree/main
**Version**: 0.1.0
**License**: Apache-2.0
**Author**: Ben Woods
**Last analyzed**: 2026-03-05

## Overview

A Python wrapper around the Smartcom FiLIP API that powers Gabb kids' smartwatches and smartphones. The API itself has no public documentation -- this library was reverse-engineered from the Gabb iOS app's network traffic.

---

## 1. Dependencies

| Package | Version |
|---------|---------|
| Python | >= 3.11 |
| requests | >= 2.31.0 |
| python-dateutil | >= 2.8.2 |

---

## 2. Architecture

The library has 4 source files:

```
gabb/
  __init__.py    - Package init, exports GabbClient
  auth.py        - GabbAuth class (requests.auth.AuthBase)
  session.py     - GabbSession class (requests.Session subclass)
  client.py      - GabbClient class (main API wrapper)
```

**Flow**: `GabbClient` creates a `GabbSession`, which uses `GabbAuth` for automatic token management. All methods return raw `requests.Response` objects.

---

## 3. Authentication

### Mechanism

- Username/password authentication against a custom SSO endpoint
- Returns access token, refresh token, and expiration date
- Tokens auto-refresh when expired (checked on every request)
- Implemented as a `requests.auth.AuthBase` subclass for transparent auth

### Auth Endpoints

| Purpose | Method | URL |
|---------|--------|-----|
| Initial auth (SSO) | POST | `https://api.myfilip.com/v2/sso/gabb` |
| Token refresh | POST | `https://api.myfilip.com/v2/token/refresh` |

### Auth Request - Initial Login

```
POST https://api.myfilip.com/v2/sso/gabb
Content-Type: application/json

{
    "appBuild": "1.28 (966)",
    "username": "<email>",
    "password": "<password>"
}
```

### Auth Request - Token Refresh

```
POST https://api.myfilip.com/v2/token/refresh
Content-Type: application/json

{
    "refreshToken": "<refresh_token>"
}
```

### Auth Response Structure

Both endpoints return the same structure:

```json
{
    "data": {
        "accessToken": "<jwt_token>",
        "refreshToken": "<refresh_token>",
        "expDate": "<ISO8601_datetime>"
    }
}
```

### Required Headers (all requests)

```python
{
    "X-Accept-Language": "en-US",
    "X-Accept-Offset": "-5.000000",
    "Accept-Version": "1.0",
    "User-Agent": "FiLIP-iOS",
    "X-Accept-Version": "1.0",
    "Content-Type": "application/json",
}
```

After authentication, all requests include:
```
Authorization: Bearer <access_token>
```

### Token Expiration Check

The library compares `expDate` (parsed via `python-dateutil`) against `datetime.datetime.now(datetime.timezone.utc)`. If expired, it calls the refresh endpoint automatically before the actual API request is made.

### GabbAuth Class (auth.py) - Key Code

```python
class GabbAuth(requests.auth.AuthBase):
    _access_token = ""
    _refresh_token = ""
    _exp_date = ""
    _required_headers = {
        "X-Accept-Language": "en-US",
        "X-Accept-Offset": "-5.000000",
        "Accept-Version": "1.0",
        "User-Agent": "FiLIP-iOS",
        "X-Accept-Version": "1.0",
        "Content-Type": "application/json",
    }

    def __init__(
        self,
        username: str,
        password: str,
        auth_url: str = "https://api.myfilip.com/v2/sso/gabb",
        refresh_url: str = "https://api.myfilip.com/v2/token/refresh",
        app_build: str = "1.28 (966)",
    ) -> None:
        self.username = username
        self.password = password
        self.auth_url = auth_url
        self.refresh_url = refresh_url
        self.app_build = app_build
        self._new_authentication()

    def __call__(self, request):
        if self._token_expired:
            self._refresh_authentication()
        request.headers.update({"Authorization": f"Bearer {self._access_token}"})
        return request

    def _new_authentication(self):
        payload = json.dumps({
            "appBuild": self.app_build,
            "username": self.username,
            "password": self.password,
        })
        resp = requests.post(self.auth_url, headers=self._required_headers, data=payload, timeout=15)
        self._update_tokens_from_response(response=resp)

    def _refresh_authentication(self):
        payload = json.dumps({"refreshToken": self._refresh_token})
        resp = requests.post(self.refresh_url, headers=self._required_headers, data=payload, timeout=15)
        self._update_tokens_from_response(response=resp)

    def _update_tokens_from_response(self, response):
        resp_data = response.json()
        self._access_token = resp_data["data"]["accessToken"]
        self._refresh_token = resp_data["data"]["refreshToken"]
        self._exp_date = parser.parse(resp_data["data"]["expDate"])

    @property
    def _token_expired(self):
        return self._exp_date < datetime.datetime.now(datetime.timezone.utc)
```

---

## 4. Session Management (session.py)

```python
class GabbSession(requests.Session):
    def __init__(self, username, password, base_url=None, alt_base_url=None):
        super().__init__()
        self.base_url = base_url
        self.alt_base_url = alt_base_url
        self.use_alt_base_url_next_request = False
        self.auth = GabbAuth(username=username, password=password)

    def request(self, method, url, *args, **kwargs):
        if self.use_alt_base_url_next_request:
            joined_url = urljoin(self.alt_base_url, url)
            self.use_alt_base_url_next_request = False
        else:
            joined_url = urljoin(self.base_url, url)
        return super().request(method, joined_url, *args, **kwargs)
```

---

## 5. Base URLs

| URL | Usage |
|-----|-------|
| `https://api.myfilip.com/v2/` | Primary base URL for most endpoints |
| `https://api.myfilip.com/` | Alternative base URL for safezone endpoints only |

The `GabbSession` manages both URLs. Safezone methods set `use_alt_base_url_next_request = True` before making requests, which causes the session to use the alt base URL for that single request, then revert.

---

## 6. Complete API Endpoints

### 6.1 Location / Map

#### GET map
**Endpoint**: `GET /v2/map`
**Purpose**: Get device geolocation data and general device info for ALL devices on the account.
**Parameters**: None
**Notes**: This is the primary way to get device IDs, locations, battery levels, and device metadata. Returns data for all devices associated with the parent account.

#### POST map/refresh/{device_id}
**Endpoint**: `POST /v2/map/refresh/{device_id}`
**Purpose**: Force a location refresh for a specific device.
**Parameters**: `device_id` (int) - in URL path
**Notes**: Triggers the device to report its current location. The updated location can then be retrieved via `GET /v2/map`.

### 6.2 User Profile

#### GET user/profile
**Endpoint**: `GET /v2/user/profile`
**Purpose**: Get the parent/guardian user profile.
**Parameters**: None

### 6.3 Device Profile

#### GET device/profile/{device_id}
**Endpoint**: `GET /v2/device/profile/{device_id}`
**Purpose**: Get the profile for a specific device (child info).
**Parameters**: `device_id` (int) - in URL path

#### PUT device/update-profile/{device_id}
**Endpoint**: `PUT /v2/device/update-profile/{device_id}`
**Purpose**: Update the child's profile on a device.
**Parameters**:

```json
{
    "firstName": "string",
    "lastName": "string",
    "gender": 1,
    "birthDate": 1430784000000
}
```

**Notes**:
- `gender`: 1 = male, 2 = female
- `birthDate`: Unix timestamp in **milliseconds** (UTC)
- All fields are optional; only include fields to update

### 6.4 Device Settings

#### GET settings/{device_id}
**Endpoint**: `GET /v2/settings/{device_id}`
**Purpose**: Get all settings for a specific device.
**Parameters**: `device_id` (int) - in URL path

#### PUT settings/{device_id}
**Endpoint**: `PUT /v2/settings/{device_id}`
**Purpose**: Update device settings.
**Parameters** (all optional, camelCase in API):

| Parameter | Type | Description |
|-----------|------|-------------|
| activeTrackingEnable | bool | Enable high-frequency tracking |
| activeTrackingDuration | int | Duration of active tracking in seconds |
| activeTrackingFrequency | int | Active tracking interval in seconds |
| batteryPowerSavingMode | bool | Enable/disable battery saving mode |
| trackingEnabled | bool | Enable/disable location tracking |
| trackingStartTime | string | Daily tracking start time (HH:MM format, truncated from HH:MM:SS) |
| trackingEndTime | string | Daily tracking end time (HH:MM format) |
| trackingInterval | int | Standard tracking interval in seconds |
| silentMode | bool | Enable/disable silent mode |

### 6.5 Contacts

#### GET contact
**Endpoint**: `GET /v2/contact`
**Purpose**: Get all contacts for the account.
**Parameters**: None

#### POST contact
**Endpoint**: `POST /v2/contact`
**Purpose**: Add a new contact.
**Payload**:

```json
{
    "firstName": "string",
    "lastName": "string",
    "phone": "+15555555555",
    "relationship": "Friend",
    "devices": [555555],
    "photo": "",
    "emergency": false,
    "enableChatSchoolMode": false,
    "guest": false,
    "guestPrimaryAccess": false
}
```

**Notes**:
- `phone`: Full international format (e.g., "+15555555555")
- `devices`: Array of device IDs to associate the contact with
- `photo`: String-encoded photo (encoding format undocumented)
- No `update_contact()` method exists in the library

#### DELETE contact/{contact_id}
**Endpoint**: `DELETE /v2/contact/{contact_id}`
**Purpose**: Delete a contact.
**Parameters**: `contact_id` (int) - in URL path

#### GET contact/emergency
**Endpoint**: `GET /v2/contact/emergency`
**Purpose**: Get emergency contacts for all devices.
**Parameters**: None

#### PUT contact/emergency/{device_id}
**Endpoint**: `PUT /v2/contact/emergency/{device_id}`
**Purpose**: Set the emergency contact for a specific device.
**Payload**:

```json
{
    "contactId": 12345,
    "isTemplate": false
}
```

### 6.6 Goals

#### GET device/goals/{device_id}
**Endpoint**: `GET /v2/device/goals/{device_id}`
**Purpose**: Get goals (step goals) for a device.
**Parameters**: `device_id` (int) - in URL path

#### POST device/goals/{device_id}
**Endpoint**: `POST /v2/device/goals/{device_id}`
**Purpose**: Set the step goal for a device.
**Payload**:

```json
{
    "stepGoal": 10000
}
```

### 6.7 Event Logs

#### GET eventlogs
**Endpoint**: `GET /v2/eventlogs`
**Purpose**: Get all event log entries.
**Parameters**: None

#### DELETE eventlogs
**Endpoint**: `DELETE /v2/eventlogs`
**Purpose**: Delete ALL event log entries.
**Parameters**: None

#### GET eventlogs/count
**Endpoint**: `GET /v2/eventlogs/count`
**Purpose**: Get the count of event log entries.
**Parameters**: None

### 6.8 Lock Mode Schedules (Alarms API)

**Note**: Gabb repurposes the FiLIP "alarms" API for lock mode schedules. The endpoint name is `alarms` but it controls lock mode/school mode.

#### GET alarms
**Endpoint**: `GET /v2/alarms`
**Purpose**: Get all lock mode schedules.
**Parameters**: None

#### POST alarms
**Endpoint**: `POST /v2/alarms`
**Purpose**: Create a new lock mode schedule.
**Payload** (TitleCase keys):

```json
{
    "WeekDays": [true, true, true, true, true, false, false],
    "Name": "School Hours",
    "Devices": [555555],
    "Time": 28800,
    "EndTime": 54000,
    "Enabled": true,
    "SilentMode": false,
    "Type": 4,
    "Date": null,
    "SchoolMode": true,
    "FocusMode": false
}
```

**Notes**:
- `WeekDays`: Array of 7 booleans [Mon, Tue, Wed, Thu, Fri, Sat, Sun]
- `Time` and `EndTime`: Seconds since midnight (e.g., 28800 = 8:00 AM)
- `Type`: Always 4 for lock mode schedules
- `SchoolMode`: Always true
- `FocusMode`: Always false
- `SilentMode`: Always false
- `Date`: Always null

#### PUT alarms/{lock_mode_schedule_id}
**Endpoint**: `PUT /v2/alarms/{lock_mode_schedule_id}`
**Purpose**: Update an existing lock mode schedule.
**Payload**: Same structure as POST, with TitleCase keys.

#### DELETE alarms/{lock_mode_schedule_id}
**Endpoint**: `DELETE /v2/alarms/{lock_mode_schedule_id}`
**Purpose**: Delete a lock mode schedule.
**Parameters**: `lock_mode_schedule_id` (int) - in URL path

### 6.9 Todos

#### GET todo
**Endpoint**: `GET /v2/todo`
**Purpose**: Get all todos.
**Parameters**: None

#### DELETE todo
**Endpoint**: `DELETE /v2/todo`
**Purpose**: Delete a specific todo.
**Payload**:

```json
{
    "deviceId": 555555,
    "todoId": 12345
}
```

#### POST todo (NOT IMPLEMENTED)
**Note**: `add_todo()` raises `NotImplementedError` -- author states data structure is not fully understood.

#### PUT todo (NOT IMPLEMENTED)
**Note**: `update_todo()` raises `NotImplementedError`.

### 6.10 Text Presets

#### GET tokk/device/{device_id}/preset
**Endpoint**: `GET /v2/tokk/device/{device_id}/preset`
**Purpose**: Get text preset messages for a device.
**Parameters**: `device_id` (int) - in URL path

#### POST tokk/device/{device_id}/preset
**Endpoint**: `POST /v2/tokk/device/{device_id}/preset`
**Purpose**: Add a text preset message.
**Payload**:

```json
{
    "deviceId": 555555,
    "message": "I'm on my way home"
}
```

#### PUT tokk/device/{device_id}/preset/{preset_id}
**Endpoint**: `PUT /v2/tokk/device/{device_id}/preset/{preset_id}`
**Purpose**: Update a text preset message.
**Payload**:

```json
{
    "deviceId": 555555,
    "presetId": 12345,
    "message": "Updated message"
}
```

#### DELETE tokk/device/{device_id}/preset/{preset_id}
**Endpoint**: `DELETE /v2/tokk/device/{device_id}/preset/{preset_id}`
**Purpose**: Delete a text preset message.
**Parameters**: `device_id` and `preset_id` (int) - in URL path

### 6.11 Safezones (Geofencing)

**IMPORTANT**: Safezone endpoints use the **alternative base URL** (`https://api.myfilip.com/`) instead of the standard v2 URL. Response attributes come back in **TitleCase** instead of camelCase.

#### GET safezone/list
**Endpoint**: `GET https://api.myfilip.com/safezone/list`
**Purpose**: Get all safezones for the account.
**Parameters**: None

#### POST safezone/add
**Endpoint**: `POST https://api.myfilip.com/safezone/add`
**Purpose**: Add a new safezone.
**Payload** (TitleCase keys):

```json
{
    "Longitude": -80.48236,
    "Latitude": 48.51629,
    "Name": "Home",
    "Radius": 150.0,
    "Enabled": true,
    "Devices": [555555]
}
```

**Notes**:
- `Radius`: Likely in feet. Minimum in app is ~150. Maximum unknown.
- `Devices`: Array of device IDs this safezone applies to.

#### POST safezone/edit?zoneId={zone_id}
**Endpoint**: `POST https://api.myfilip.com/safezone/edit?zoneId={zone_id}`
**Purpose**: Update an existing safezone.
**Parameters**: `zone_id` (string) as query parameter
**Payload**: Same structure as add (TitleCase), excluding zone_id.

#### POST safezone/delete?zoneId={zone_id}
**Endpoint**: `POST https://api.myfilip.com/safezone/delete?zoneId={zone_id}`
**Purpose**: Delete a safezone.
**Parameters**: `zone_id` (string) as query parameter
**Notes**: Uses POST (not DELETE) with zone_id as query parameter. No request body.

---

## 7. Data Models

The library does NOT define explicit data model classes. All methods return raw `requests.Response` objects. The caller must call `.json()` to parse responses. Based on the API patterns, the following data structures are expected:

### 7.1 Map Response (Location + Device Info)

The `GET /v2/map` endpoint is the most important for a Home Assistant integration. Expected response structure (based on FiLIP API patterns):

```json
{
    "data": [
        {
            "deviceId": 555555,
            "firstName": "Child Name",
            "lastName": "Last Name",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "battery": 85,
            "deviceType": "...",
            "lastUpdate": "...",
            "...": "other fields TBD from live API response"
        }
    ]
}
```

Key fields likely available from map:
- Device ID
- Device name / child name
- GPS coordinates (latitude, longitude)
- Battery level
- Device type (watch vs phone)
- Last location update timestamp

### 7.2 Auth Token Response

```json
{
    "data": {
        "accessToken": "string",
        "refreshToken": "string",
        "expDate": "ISO8601 datetime string"
    }
}
```

### 7.3 Contact Object

```json
{
    "firstName": "string",
    "lastName": "string",
    "phone": "+15555555555",
    "relationship": "Friend",
    "devices": [555555],
    "photo": "",
    "emergency": false,
    "enableChatSchoolMode": false,
    "guest": false,
    "guestPrimaryAccess": false
}
```

### 7.4 Device Profile Object

```json
{
    "firstName": "string",
    "lastName": "string",
    "gender": 1,
    "birthDate": 1430784000000
}
```

### 7.5 Lock Mode Schedule Object

```json
{
    "WeekDays": [true, true, true, true, true, false, false],
    "Name": "string",
    "Devices": [555555],
    "Time": 28800,
    "EndTime": 54000,
    "Enabled": true,
    "SilentMode": false,
    "Type": 4,
    "SchoolMode": true,
    "FocusMode": false
}
```

### 7.6 Safezone Object

```json
{
    "Longitude": -80.48236,
    "Latitude": 48.51629,
    "Name": "Home",
    "Radius": 150.0,
    "Enabled": true,
    "Devices": [555555],
    "ZoneId": "string"
}
```

---

## 8. Error Handling

The library has **minimal error handling**:
- No custom exception classes
- No HTTP status code checking
- No response validation
- Raw `requests.Response` objects are returned directly
- The `requests` library will raise its own exceptions for connection errors
- Auth failures will propagate as unhandled exceptions from `response.json()` key access

For a Home Assistant integration, you will need to add:
- HTTP status code checking (401, 403, 404, 429, 500, etc.)
- JSON parse error handling
- Connection timeout handling
- Auth failure detection and re-auth logic
- Rate limiting awareness

---

## 9. Utility Methods

### convert_time_to_seconds(time: datetime.time) -> int

Converts a `datetime.time` object to the number of seconds since midnight. Used for lock mode schedule times.

```python
@staticmethod
def convert_time_to_seconds(time: datetime.time) -> int:
    return int(
        datetime.timedelta(
            hours=time.hour, minutes=time.minute, seconds=time.second
        ).total_seconds()
    )
```

### prepare_params_for_api_call(locals_, values_to_filter=None, title_case=False) -> dict

Takes a `locals()` dict from a method, filters out `self`, `None` values, and specified keys, then converts snake_case parameter names to camelCase (default) or TitleCase.

```python
@staticmethod
def prepare_params_for_api_call(locals_, values_to_filter=None, title_case=False):
    if values_to_filter is None:
        values_to_filter = []
    values_to_filter.append("self")
    filtered_locals = {}
    for key, value in locals_.items():
        if value is not None and key not in values_to_filter:
            if title_case:
                new_key = key.title().replace("_", "")
            else:
                new_key = key[0] + key.title().replace("_", "")[1:]
            filtered_locals[new_key] = value
    return filtered_locals
```

---

## 10. GabbClient Initialization

```python
class GabbClient:
    _required_headers = {
        "X-Accept-Language": "en-US",
        "X-Accept-Offset": "-5.000000",
        "Accept-Version": "1.0",
        "User-Agent": "FiLIP-iOS",
        "X-Accept-Version": "1.0",
        "Content-Type": "application/json",
    }

    def __init__(self, username, password, base_url="https://api.myfilip.com/"):
        base_url_v2 = urljoin(base_url, "v2/")
        self._session = GabbSession(
            username=username,
            password=password,
            base_url=base_url_v2,
            alt_base_url=base_url,
        )
        self._session.headers.update(self._required_headers)
```

---

## 11. Complete Method Summary Table

| Method | HTTP | Endpoint | Category |
|--------|------|----------|----------|
| `get_map()` | GET | `/v2/map` | Location |
| `refresh_map(device_id)` | POST | `/v2/map/refresh/{id}` | Location |
| `get_user_profile()` | GET | `/v2/user/profile` | User |
| `get_device_profile(device_id)` | GET | `/v2/device/profile/{id}` | Device |
| `update_device_profile(device_id, ...)` | PUT | `/v2/device/update-profile/{id}` | Device |
| `get_device_settings(device_id)` | GET | `/v2/settings/{id}` | Settings |
| `update_device_settings(device_id, ...)` | PUT | `/v2/settings/{id}` | Settings |
| `get_contacts()` | GET | `/v2/contact` | Contacts |
| `add_contact(...)` | POST | `/v2/contact` | Contacts |
| `delete_contact(contact_id)` | DELETE | `/v2/contact/{id}` | Contacts |
| `get_emergency_contact()` | GET | `/v2/contact/emergency` | Contacts |
| `set_emergency_contact(device_id, contact_id)` | PUT | `/v2/contact/emergency/{id}` | Contacts |
| `get_goals(device_id)` | GET | `/v2/device/goals/{id}` | Goals |
| `set_step_goal(device_id, step_goal)` | POST | `/v2/device/goals/{id}` | Goals |
| `get_event_log()` | GET | `/v2/eventlogs` | Events |
| `delete_event_log()` | DELETE | `/v2/eventlogs` | Events |
| `get_event_log_count()` | GET | `/v2/eventlogs/count` | Events |
| `get_lock_mode_schedules()` | GET | `/v2/alarms` | Lock Mode |
| `create_lock_mode_schedule(...)` | POST | `/v2/alarms` | Lock Mode |
| `update_lock_mode_schedule(id, ...)` | PUT | `/v2/alarms/{id}` | Lock Mode |
| `delete_lock_mode_schedule(id)` | DELETE | `/v2/alarms/{id}` | Lock Mode |
| `get_todos()` | GET | `/v2/todo` | Todos |
| `delete_todo(device_id, todo_id)` | DELETE | `/v2/todo` | Todos |
| `get_text_presets(device_id)` | GET | `/v2/tokk/device/{id}/preset` | Text |
| `add_text_preset(device_id, message)` | POST | `/v2/tokk/device/{id}/preset` | Text |
| `update_text_preset(device_id, preset_id, msg)` | PUT | `/v2/tokk/device/{id}/preset/{pid}` | Text |
| `delete_text_preset(device_id, preset_id)` | DELETE | `/v2/tokk/device/{id}/preset/{pid}` | Text |
| `get_safezones()` | GET | `/safezone/list` | Safezones |
| `add_safezone(...)` | POST | `/safezone/add` | Safezones |
| `update_safezone(zone_id, ...)` | POST | `/safezone/edit?zoneId={id}` | Safezones |
| `delete_safezone(zone_id)` | POST | `/safezone/delete?zoneId={id}` | Safezones |

---

## 12. Key Implementation Details for Home Assistant

### 12.1 Async Conversion Required

The library uses synchronous `requests.Session`. For Home Assistant, all HTTP calls must be converted to `aiohttp` (async). The auth flow, token refresh, and all API calls need async equivalents.

### 12.2 Parameter Naming Conventions

The API uses mixed conventions:
- Most endpoints: **camelCase** (e.g., `firstName`, `trackingInterval`)
- Lock mode schedules: **TitleCase** (e.g., `WeekDays`, `Devices`)
- Safezone endpoints: **TitleCase** (e.g., `Longitude`, `Latitude`, `Name`)

### 12.3 Time Handling

- Lock mode times: Seconds since midnight (int)
- Tracking times: "HH:MM" string format (truncated from HH:MM:SS)
- Birth dates: Unix timestamp in milliseconds
- Token expiration: ISO 8601 datetime string (parsed with `python-dateutil`)

### 12.4 Device IDs

- Device IDs are integers
- The primary way to discover device IDs is via `GET /v2/map`
- Device IDs are used in most endpoint paths

### 12.5 Safezone Zone IDs

- Zone IDs are strings (not integers)
- Passed as query parameters, not path parameters
- Safezone delete/edit use POST (not DELETE/PUT)

### 12.6 Polling Strategy for HA

For a Home Assistant integration, the recommended polling approach:
1. Call `GET /v2/map` periodically (e.g., every 30-120 seconds) for location and battery
2. Call `POST /v2/map/refresh/{device_id}` to force a fresh location from the device
3. Call `GET /v2/settings/{device_id}` less frequently for settings state
4. Safezone and contact data changes infrequently; poll every few minutes or on demand

### 12.7 HA Entity Mapping Suggestions

| Entity Type | Data Source | Attributes |
|------------|-------------|------------|
| `device_tracker` | `GET /v2/map` | latitude, longitude, battery, GPS accuracy |
| `sensor` (battery) | `GET /v2/map` | battery percentage |
| `sensor` (steps) | `GET /v2/device/goals/{id}` | step count, step goal |
| `switch` (silent mode) | `GET/PUT /v2/settings/{id}` | on/off |
| `switch` (tracking) | `GET/PUT /v2/settings/{id}` | on/off |
| `switch` (power saving) | `GET/PUT /v2/settings/{id}` | on/off |
| `binary_sensor` (lock mode) | `GET /v2/alarms` | active/inactive based on schedule |

---

## 13. Capabilities NOT Present in Library

The following capabilities are **not implemented** but may exist in the FiLIP API:
- Sending messages/texts to the device
- Reading message history
- SOS/panic alert management
- Firmware update status
- Call history
- App management (for Gabb phones)
- Adding/updating todos (stubs exist but raise NotImplementedError)
- Updating existing contacts (no method exists)
- Real-time push notifications / webhooks
