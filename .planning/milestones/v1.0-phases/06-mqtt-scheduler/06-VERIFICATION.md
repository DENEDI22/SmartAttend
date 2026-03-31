---
phase: 06-mqtt-scheduler
verified: 2026-03-30T09:00:00Z
status: passed
score: 5/5 must-haves verified
re_verification: false
---

# Phase 6: MQTT & Scheduler Verification Report

**Phase Goal:** The server issues time-limited tokens to devices on a schedule and tracks device state via MQTT
**Verified:** 2026-03-30T09:00:00Z
**Status:** passed
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths (from ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A new device registration message auto-creates a device record with is_enabled=False | VERIFIED | mqtt.py:65 `Device(device_id=device_id, is_enabled=False, is_online=False)`, test_register_device_json passes |
| 2 | Heartbeat messages update is_online and last_seen; lux messages update last_lux | VERIFIED | mqtt.py:80-81 sets is_online/last_seen, mqtt.py:94 sets last_lux, both tests pass |
| 3 | Scheduler runs every minute and publishes token URL to each active, enabled device with format http://{SERVER_IP}/checkin?token={uuid} | VERIFIED | scheduler.py:112-116 IntervalTrigger(minutes=1), scheduler.py:77 URL format, test_token_url_format validates UUID |
| 4 | When a new token is issued for a device, the previous token is deactivated | VERIFIED | scheduler.py:57-60 bulk update is_active=False, test_deactivate_previous_token confirms old token deactivated |
| 5 | Tokens expire at the lesson's end_time | VERIFIED | scheduler.py:71 `expires_at=datetime.combine(today, entry.end_time)`, test_token_expiry confirms |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `app/services/mqtt.py` | MQTT client with callbacks and publish_token | VERIFIED | 134 lines, exports start_mqtt, stop_mqtt, publish_token; handlers for register/heartbeat/lux |
| `app/services/scheduler.py` | APScheduler with token issuance and heartbeat monitor | VERIFIED | 134 lines, exports start_scheduler, stop_scheduler; _issue_tokens and _check_heartbeats jobs |
| `tests/test_mqtt.py` | Unit tests for all MQTT handlers (min 80 lines) | VERIFIED | 132 lines, 7 test functions, all passing |
| `tests/test_scheduler.py` | Unit tests for scheduler logic (min 80 lines) | VERIFIED | 293 lines, 8 test functions, all passing |
| `app/main.py` | Lifespan wiring for MQTT and scheduler | VERIFIED | Imports start_mqtt/stop_mqtt/start_scheduler/stop_scheduler, correct start/stop ordering |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| app/services/mqtt.py | app/database.SessionLocal | Each callback creates own session | WIRED | SessionLocal() called in _handle_register (line 60), _handle_heartbeat (line 75), _handle_lux (line 89) |
| app/services/mqtt.py | app/models/device.py | Query and create Device records | WIRED | Device imported (line 10), used in queries and creation across all handlers |
| app/services/scheduler.py | app/services/mqtt.publish_token | Import and call after token creation | WIRED | Imported on line 14, called on line 78 |
| app/main.py | app/services/mqtt.start_mqtt | Called in lifespan startup | WIRED | Imported on line 8, called on line 46 |
| app/main.py | app/services/scheduler.start_scheduler | Called in lifespan startup | WIRED | Imported on line 9, called on line 47 |
| app/main.py shutdown | stop_scheduler before stop_mqtt | Correct ordering after yield | WIRED | Lines 49-50: stop_scheduler() then stop_mqtt() |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| scheduler.py _issue_tokens | entries (ScheduleEntry list) | DB query with join on Device, filtered by weekday/time/enabled | Yes -- real SQLAlchemy query | FLOWING |
| scheduler.py _issue_tokens | token_str | uuid.uuid4() | Yes -- generates real UUIDs | FLOWING |
| mqtt.py _handle_register | device_id | MQTT message payload (JSON or raw) | Yes -- creates real Device record | FLOWING |
| mqtt.py publish_token | url | Constructed from settings.server_ip + token_str | Yes -- publishes via paho client | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| MQTT tests pass | pytest tests/test_mqtt.py -v | 7 passed | PASS |
| Scheduler tests pass | pytest tests/test_scheduler.py -v | 8 passed | PASS |
| Full suite no regressions | pytest tests/ -x -q | 71 passed, 1 xfailed | PASS |
| mqtt.py exports correct functions | grep "def start_mqtt\|def stop_mqtt\|def publish_token" | All 3 found | PASS |
| scheduler.py exports correct functions | grep "def start_scheduler\|def stop_scheduler" | Both found | PASS |
| V2 callback API used | grep CallbackAPIVersion.VERSION2 mqtt.py | Found on line 114 | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| MQTT-01 | 06-01 | Server subscribes to devices/register, devices/+/status, sensors/+/lux | SATISFIED | mqtt.py:20-24 subscribe call with all 3 topic patterns |
| MQTT-02 | 06-01 | Registration message auto-creates device with is_enabled=False | SATISFIED | mqtt.py:65 Device creation, test_register_device_json |
| MQTT-03 | 06-01 | Heartbeat updates is_online and last_seen | SATISFIED | mqtt.py:80-81, test_heartbeat_update |
| MQTT-04 | 06-01 | Sensor message updates last_lux | SATISFIED | mqtt.py:94, test_lux_update |
| MQTT-05 | 06-01 | publish_token publishes to attendance/device/{device_id} | SATISFIED | mqtt.py:103-107 with QoS 1, test_publish_token |
| MQTT-06 | 06-02 | Scheduler runs every minute and issues tokens for active enabled entries | SATISFIED | scheduler.py:112-116 IntervalTrigger(minutes=1), _issue_tokens filters by enabled+active |
| MQTT-07 | 06-02 | New token deactivates previous active token | SATISFIED | scheduler.py:57-60, test_deactivate_previous_token |
| MQTT-08 | 06-02 | Token URL format http://{SERVER_IP}/checkin?token={uuid} | SATISFIED | scheduler.py:77, test_token_url_format validates format and UUID |
| MQTT-09 | 06-02 | Token expires at lesson end_time | SATISFIED | scheduler.py:71 datetime.combine(today, entry.end_time), test_token_expiry |

All 9 requirements satisfied. No orphaned requirements found.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | - | - | - | - |

No TODOs, FIXMEs, placeholders, empty returns, or stub patterns found in phase artifacts.

### Human Verification Required

### 1. MQTT Broker Integration

**Test:** Start the app with a running Mosquitto broker; publish a registration message to devices/register and verify a Device appears in the database.
**Expected:** Device record created with is_enabled=False, is_online=False.
**Why human:** Requires a live MQTT broker; unit tests mock the paho client.

### 2. Token Delivery End-to-End

**Test:** With a running app, create a device + schedule entry for the current time; wait 60 seconds for the scheduler to fire; check that the device receives a token URL via MQTT.
**Expected:** Token URL published to attendance/device/{device_id} topic; token record in DB with correct expires_at.
**Why human:** Requires running infrastructure (MQTT broker, scheduler timing).

### 3. Heartbeat Timeout

**Test:** Publish a heartbeat, wait >90 seconds without another heartbeat; verify device is marked offline.
**Expected:** Device is_online transitions from True to False after 90s.
**Why human:** Requires real timing behavior with running scheduler.

### Gaps Summary

No gaps found. All 5 observable truths verified, all 9 requirements satisfied, all artifacts exist and are substantive and wired, all 15 phase-specific tests pass, full suite of 71 tests passes with no regressions. The phase goal of "the server issues time-limited tokens to devices on a schedule and tracks device state via MQTT" is achieved.

---

_Verified: 2026-03-30T09:00:00Z_
_Verifier: Claude (gsd-verifier)_
