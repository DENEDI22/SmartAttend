---
phase: 07-dummy-clients
plan: 01
subsystem: mqtt
tags: [paho-mqtt, mqtt, dummy-client, esp32-simulator, threading]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: "dummy_client/ directory structure and Docker Compose services"
provides:
  - "Full paho-mqtt v2 dummy client replacing Phase 1 stub"
  - "Unit tests for all 5 MQTT behaviors (DUMMY-01 through DUMMY-05)"
affects: [07-dummy-clients]

# Tech tracking
tech-stack:
  added: []
  patterns: [paho-mqtt-v2-callbacks, threading-event-shutdown, importlib-reload-testing]

key-files:
  created:
    - tests/test_dummy_client.py
  modified:
    - dummy_client/main.py

key-decisions:
  - "Used importlib.reload with sys.path for testing standalone dummy_client module"
  - "stop_event.wait() pattern for both graceful shutdown and testable periodic loops"

patterns-established:
  - "paho-mqtt v2 callback signatures: on_connect(client, userdata, connect_flags, reason_code, properties)"
  - "Module-level threading.Event for graceful SIGTERM/SIGINT shutdown"
  - "Daemon threads for periodic publish loops (heartbeat 30s, lux 60s)"

requirements-completed: [DUMMY-01, DUMMY-02, DUMMY-03, DUMMY-04, DUMMY-05]

# Metrics
duration: 5min
completed: 2026-03-30
---

# Phase 7 Plan 1: Dummy MQTT Client Summary

**paho-mqtt v2 dummy client publishing registration, heartbeat (30s), lux (60s), subscribing to token URLs with graceful SIGTERM shutdown**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-30T08:53:03Z
- **Completed:** 2026-03-30T08:58:17Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Replaced Phase 1 stub with full paho-mqtt v2 client matching server MQTT contract
- Registration JSON published to devices/register on connect, subscription to attendance/device/{id}
- Heartbeat (30s) and lux (60s) periodic loops via daemon threads with stop_event
- 6 unit tests covering all 5 DUMMY requirements plus robustness case

## Task Commits

Each task was committed atomically:

1. **Task 1: Create test scaffold for dummy client** - `5a1a079` (test)
2. **Task 2: Implement full dummy MQTT client** - `c68c171` (feat)

## Files Created/Modified
- `tests/test_dummy_client.py` - 6 unit tests for env config, registration, heartbeat, lux, token URL logging, and connect failure
- `dummy_client/main.py` - Full paho-mqtt v2 client with registration, heartbeat, lux, token subscription, and SIGTERM shutdown

## Decisions Made
- Used `importlib.reload` with `sys.path.insert` for testing the standalone dummy_client module (not a package)
- `stop_event.wait(timeout)` pattern serves dual purpose: sleep interval for periodic loops and testability via monkeypatch
- Both tasks committed together since Phase 1 stub's infinite loop prevents RED-phase test execution (tests would hang on import)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Phase 1 stub has `while True: time.sleep(60)` at module level, making imports hang -- tests cannot run in RED phase against the stub. Both tasks were implemented and committed in sequence without a RED verification step.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None - all functionality is fully wired.

## Next Phase Readiness
- Dummy client ready for Docker Compose integration testing
- Token URL subscription will receive URLs from scheduler's publish_token calls
- Plan 07-02 can build on this for Docker Compose wiring and multi-client orchestration

---
*Phase: 07-dummy-clients*
*Completed: 2026-03-30*
