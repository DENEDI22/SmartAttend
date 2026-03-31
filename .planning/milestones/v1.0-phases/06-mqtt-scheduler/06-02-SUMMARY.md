---
phase: 06-mqtt-scheduler
plan: 02
subsystem: scheduler
tags: [apscheduler, token-lifecycle, heartbeat, mqtt-integration]

# Dependency graph
requires:
  - phase: 06-01
    provides: MQTT client service with publish_token function
  - phase: 01-foundation
    provides: Device, ScheduleEntry, AttendanceToken models, database SessionLocal
provides:
  - APScheduler background service with token issuance (1min) and heartbeat monitor (30s)
  - FastAPI lifespan wiring for MQTT and scheduler lifecycle
affects: [07-dummy-clients]

# Tech tracking
tech-stack:
  added: [APScheduler 3.11.2]
  patterns: [BackgroundScheduler with IntervalTrigger, max_instances=1 job overlap prevention, NonClosingSession test pattern]

key-files:
  created: [app/services/scheduler.py, tests/test_scheduler.py]
  modified: [app/services/mqtt.py, app/main.py]

key-decisions:
  - "NonClosingSession pattern reused from test_mqtt.py for scheduler DB test isolation"
  - "mqtt.py start_mqtt wraps connect in try/except for graceful degradation when broker unavailable"
  - "Scheduler starts after MQTT, stops before MQTT (dependency ordering in lifespan)"

patterns-established:
  - "Scheduler job pattern: each job creates own SessionLocal(), try/except/finally for rollback and close"
  - "Token deactivation before creation: bulk update is_active=False then insert new token"

requirements-completed: [MQTT-06, MQTT-07, MQTT-08, MQTT-09]

# Metrics
duration: 176s
completed: 2026-03-30
---

# Phase 6 Plan 2: Scheduler Service Summary

**APScheduler with 1-minute token issuance for active lessons and 30-second heartbeat timeout monitoring, wired into FastAPI lifespan**

## Performance

- **Duration:** 176s (~3 min)
- **Started:** 2026-03-30T08:26:20Z
- **Completed:** 2026-03-30T08:29:16Z
- **Tasks:** 2 (Task 1: TDD RED+GREEN, Task 2: lifespan wiring)
- **Files created:** 2 (scheduler.py, test_scheduler.py)
- **Files modified:** 2 (mqtt.py, main.py)

## Accomplishments

- Scheduler issues tokens every minute for enabled devices with active schedule entries
- Previous active tokens deactivated before new token creation (prevents stale URLs)
- Token URL format: `http://{SERVER_IP}/checkin?token={uuid}`
- Token expires_at equals datetime.combine(today, schedule_entry.end_time)
- Heartbeat monitor checks every 30s, marks devices offline after 90s without heartbeat
- MQTT and scheduler wired into FastAPI lifespan with correct start/stop ordering
- mqtt.py connect wrapped in try/except for graceful handling when broker unavailable
- 8 scheduler tests + full suite of 32 tests passing

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing scheduler tests** - `5be5057` (test)
2. **Task 1 (GREEN): Scheduler service implementation** - `7cbb31a` (feat)
3. **Task 2: Lifespan wiring** - `43f25dd` (feat)

## Files Created/Modified

- `app/services/scheduler.py` - APScheduler service with _issue_tokens, _check_heartbeats, start/stop lifecycle
- `tests/test_scheduler.py` - 8 unit tests covering token issuance and heartbeat monitoring
- `app/services/mqtt.py` - Added try/except around connect for graceful broker unavailability
- `app/main.py` - Added start_mqtt/start_scheduler on startup, stop_scheduler/stop_mqtt on shutdown

## Decisions Made

- Reused NonClosingSession wrapper pattern from test_mqtt.py to prevent db.close() from detaching objects during test assertions
- Wrapped mqtt.py connect in try/except so tests and environments without a broker don't crash on startup
- Start order: MQTT before scheduler (scheduler publishes via MQTT); Stop order: scheduler before MQTT

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed APScheduler dependency**
- **Found during:** Task 1 (before RED phase)
- **Issue:** apscheduler not installed in development environment
- **Fix:** pip install apscheduler
- **Verification:** Module imports successfully

**2. [Rule 1 - Bug] NonClosingSession wrapper for test DB session**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Scheduler's db.close() detached objects from test session, causing DetachedInstanceError
- **Fix:** Added _NonClosingSession wrapper class in test_scheduler.py (same pattern as test_mqtt.py)
- **Files modified:** tests/test_scheduler.py
- **Verification:** All 8 tests pass

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes necessary for test execution. No scope creep.

## Known Stubs

None -- all functionality fully wired.

## Issues Encountered

None beyond the auto-fixed items above.

## Next Phase Readiness

- Token lifecycle is complete: scheduler issues tokens, publishes via MQTT, deactivates old tokens
- Heartbeat monitoring active: stale devices marked offline automatically
- Ready for Phase 7 (dummy clients) to receive tokens via MQTT subscription

## Self-Check: PASSED

All files and commits verified:
- app/services/scheduler.py: FOUND
- tests/test_scheduler.py: FOUND
- app/services/mqtt.py: FOUND
- app/main.py: FOUND
- Commit 5be5057 (RED): FOUND
- Commit 7cbb31a (GREEN): FOUND
- Commit 43f25dd (lifespan): FOUND

---
*Phase: 06-mqtt-scheduler*
*Completed: 2026-03-30*
