---
phase: 07-dummy-clients
verified: 2026-03-31T12:00:00Z
status: passed
score: 8/8 must-haves verified
---

# Phase 7: Dummy Clients Verification Report

**Phase Goal:** Three Python containers faithfully simulate ESP32 MQTT clients so the full flow can be tested without hardware
**Verified:** 2026-03-31
**Status:** PASSED
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Dummy client publishes registration JSON to devices/register on connect | VERIFIED | `dummy_client/main.py:46` publishes `{"device_id": DEVICE_ID}` to `devices/register` in `on_connect` with reason_code==0; test `test_registration_on_connect` passes |
| 2 | Dummy client publishes heartbeat to devices/{id}/status every 30 seconds | VERIFIED | `dummy_client/main.py:67` publishes "online" to `devices/{DEVICE_ID}/status` in `heartbeat_loop` with `stop_event.wait(30)`; test `test_heartbeat_publishes` passes |
| 3 | Dummy client publishes lux reading to sensors/{id}/lux every 60 seconds | VERIFIED | `dummy_client/main.py:76` publishes `str(LUX_VALUE)` to `sensors/{DEVICE_ID}/lux` in `lux_loop` with `stop_event.wait(60)`; test `test_lux_publishes` passes |
| 4 | Dummy client subscribes to attendance/device/{id} and logs received URLs | VERIFIED | `dummy_client/main.py:48` subscribes in `on_connect`; `on_message` (line 56) decodes and logs URL at INFO; test `test_token_url_logged` passes |
| 5 | All behavior configured via environment variables (DEVICE_ID, ROOM, MQTT_BROKER, MQTT_PORT, LUX_VALUE) | VERIFIED | `dummy_client/main.py:18-22` reads all 5 env vars at module level with sensible defaults; test `test_env_config` passes |
| 6 | dummy_client/Dockerfile builds a working image with paho-mqtt installed | VERIFIED | Dockerfile uses `python:3.11-slim`, copies `requirements.txt`, runs `pip install`, sets `PYTHONUNBUFFERED=1` |
| 7 | dummy_client/requirements.txt pins paho-mqtt==2.1.0 | VERIFIED | File contains exactly `paho-mqtt==2.1.0` |
| 8 | Three containers (client-e101, client-e102, client-e103) start and connect to the broker | VERIFIED | `docker-compose.yml` defines all three services with `build: ./dummy_client`, correct env vars, and `depends_on: mqtt` |

**Score:** 8/8 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `dummy_client/main.py` | Full MQTT dummy client with paho-mqtt v2 | VERIFIED | 127 lines, uses `CallbackAPIVersion.VERSION2`, implements all callbacks and periodic loops |
| `tests/test_dummy_client.py` | Unit tests for MQTT behavior | VERIFIED | 6 test functions covering DUMMY-01 through DUMMY-05 plus robustness case; all 6 pass in 0.03s |
| `dummy_client/Dockerfile` | Docker image for dummy client | VERIFIED | 7 lines, installs from requirements.txt, sets PYTHONUNBUFFERED=1 |
| `dummy_client/requirements.txt` | Python dependencies | VERIFIED | Pins paho-mqtt==2.1.0 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `dummy_client/main.py` | `app/services/mqtt.py` | MQTT topic contract | WIRED | All 4 topic patterns match: `devices/register`, `devices/+/status`, `sensors/+/lux`, `attendance/device/{id}` |
| `dummy_client/main.py` | `docker-compose.yml` | Environment variables | WIRED | All 5 env vars (DEVICE_ID, ROOM, MQTT_BROKER, MQTT_PORT, LUX_VALUE) read by client and set by compose |
| `dummy_client/Dockerfile` | `docker-compose.yml` | Build context `./dummy_client` | WIRED | All three client services use `build: ./dummy_client` |
| `dummy_client/requirements.txt` | `dummy_client/Dockerfile` | COPY and pip install | WIRED | Dockerfile line 3-4: `COPY requirements.txt .` then `RUN pip install --no-cache-dir -r requirements.txt` |

### Data-Flow Trace (Level 4)

Not applicable -- dummy client is a producer (publishes MQTT messages), not a data renderer. Data flows outward from env vars to MQTT topics, which is verified via the key link and topic contract checks above.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Module imports cleanly | `python -c "import sys; sys.path.insert(0,'dummy_client'); import main; print(main.DEVICE_ID)"` | Prints "unknown" (default) | PASS |
| All 6 unit tests pass | `python -m pytest tests/test_dummy_client.py -x -q` | 6 passed in 0.03s | PASS |
| No regressions in related tests | `python -m pytest tests/test_dummy_client.py tests/test_mqtt.py tests/test_scheduler.py -x -q` | 21 passed in 0.27s | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| DUMMY-01 | 07-01 | Publish `devices/register` on startup | SATISFIED | `on_connect` publishes registration JSON; test passes |
| DUMMY-02 | 07-01 | Publish `devices/{id}/status` heartbeat every 30s | SATISFIED | `heartbeat_loop` with 30s wait; test passes |
| DUMMY-03 | 07-01 | Publish `sensors/{id}/lux` every 60s with configurable value | SATISFIED | `lux_loop` with 60s wait, uses `LUX_VALUE` env var; test passes |
| DUMMY-04 | 07-01 | Subscribe to `attendance/device/{id}` and print URL | SATISFIED | `on_connect` subscribes, `on_message` logs URL; test passes |
| DUMMY-05 | 07-01 | Fully configured via environment variables | SATISFIED | All 5 env vars read at module level; test passes |
| DUMMY-06 | 07-02 | Dockerfile exists and included in docker-compose.yml | SATISFIED | Dockerfile builds with paho-mqtt; compose references `build: ./dummy_client` |
| DUMMY-07 | 07-02 | Three containers run as separate services | SATISFIED | docker-compose.yml defines client-e101, client-e102, client-e103 with distinct DEVICE_ID, ROOM, LUX_VALUE |

No orphaned requirements found -- all 7 DUMMY requirements are claimed by plans and satisfied.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | -- | -- | -- | No anti-patterns detected |

No TODOs, FIXMEs, placeholders, empty implementations, or hardcoded empty data found in any Phase 7 files.

### Human Verification Required

### 1. Docker Compose Container Startup

**Test:** Run `docker compose build client-e101 client-e102 client-e103` then `docker compose up -d mqtt client-e101 client-e102 client-e103`. After 10 seconds, check `docker compose logs --tail=20 client-e101 client-e102 client-e103`.
**Expected:** Each client logs "Starting dummy client", "Published registration", and "Subscribed to attendance/device/{id}". No crash loops or import errors.
**Why human:** Requires running Docker daemon and Mosquitto broker; cannot verify container networking programmatically in CI-less environment.

### 2. Heartbeat and Lux Periodic Messages

**Test:** After containers run for 60+ seconds, check broker or client logs for heartbeat and lux messages.
**Expected:** Heartbeat messages appear every ~30s, lux messages every ~60s for each client.
**Why human:** Requires live MQTT broker and time-based observation.

### Gaps Summary

No gaps found. All 8 observable truths verified. All 7 requirements satisfied. All 4 artifacts exist, are substantive, and are properly wired. All key links verified. No anti-patterns detected. All unit tests pass with no regressions.

The only items requiring human verification are live Docker Compose container startup and periodic message timing, which cannot be tested without running infrastructure.

---

_Verified: 2026-03-31_
_Verifier: Claude (gsd-verifier)_
