---
phase: 06-mqtt-scheduler
plan: 01
subsystem: mqtt
tags: [paho-mqtt, mqtt, iot, device-management]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: Device model, database SessionLocal, Settings config
provides:
  - MQTT client service with start/stop lifecycle
  - Device registration handler (creates Device from MQTT message)
  - Heartbeat handler (updates is_online, last_seen)
  - Lux sensor handler (updates last_lux)
  - publish_token function for outbound token delivery (QoS 1)
affects: [06-02-scheduler, 07-dummy-clients]

# Tech tracking
tech-stack:
  added: [paho-mqtt 2.1.0]
  patterns: [paho CallbackAPIVersion.VERSION2, per-callback SessionLocal pattern, threaded MQTT loop]

key-files:
  created: [app/services/mqtt.py, tests/test_mqtt.py]
  modified: []

key-decisions:
  - "NonClosingSession wrapper in tests to prevent db.close() from detaching objects during assertion"
  - "JSON payload with fallback to raw string for device registration"

patterns-established:
  - "MQTT handler pattern: each handler creates own SessionLocal(), uses try/finally for db.close()"
  - "MQTT test pattern: monkeypatch SessionLocal with NonClosingSession wrapper for DB handler tests"

requirements-completed: [MQTT-01, MQTT-02, MQTT-03, MQTT-04, MQTT-05]

# Metrics
duration: 3min
completed: 2026-03-30
---

# Phase 6 Plan 1: MQTT Service Summary

**Paho MQTT service with device registration, heartbeat/lux handlers, and QoS 1 token publishing via threaded background loop**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-30T08:20:40Z
- **Completed:** 2026-03-30T08:23:21Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 2

## Accomplishments
- MQTT client subscribes to 3 topic patterns on connect (devices/register, devices/+/status, sensors/+/lux)
- Registration handler creates Device records idempotently with is_enabled=False
- Heartbeat and lux handlers update device state via own SessionLocal sessions
- publish_token delivers token URLs to attendance/device/{id} with QoS 1
- 7 unit tests covering all handlers and publish function

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Test scaffold** - `0005f7f` (test)
2. **Task 1 (GREEN): MQTT service implementation** - `4ba4bf7` (feat)

_TDD task: RED committed failing tests, GREEN committed passing implementation_

## Files Created/Modified
- `app/services/mqtt.py` - MQTT client service with handlers and publish_token
- `tests/test_mqtt.py` - 7 unit tests for MQTT service

## Decisions Made
- Used NonClosingSession wrapper pattern in tests so db.close() in handlers does not detach objects from the test session during assertions
- Device registration accepts JSON payload with fallback to raw string for robustness

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed paho-mqtt dependency**
- **Found during:** Task 1 (RED phase)
- **Issue:** paho-mqtt not installed in development environment, import failed
- **Fix:** pip install paho-mqtt
- **Verification:** Module imports successfully, all tests run

**2. [Rule 1 - Bug] NonClosingSession wrapper for test DB session**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Handler db.close() detached Device objects from test session, causing InvalidRequestError on refresh
- **Fix:** Created _NonClosingSession wrapper that proxies all methods but makes close() a no-op
- **Files modified:** tests/test_mqtt.py
- **Verification:** All 7 tests pass

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes necessary for test execution. No scope creep.

## Issues Encountered
None beyond the auto-fixed items above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- MQTT service ready for integration with scheduler (Plan 06-02)
- start_mqtt/stop_mqtt can be wired into FastAPI lifespan
- publish_token ready for scheduler to call when issuing tokens to devices

## Self-Check: PASSED

All files and commits verified:
- app/services/mqtt.py: FOUND
- tests/test_mqtt.py: FOUND
- 06-01-SUMMARY.md: FOUND
- Commit 0005f7f (RED): FOUND
- Commit 4ba4bf7 (GREEN): FOUND

---
*Phase: 06-mqtt-scheduler*
*Completed: 2026-03-30*
