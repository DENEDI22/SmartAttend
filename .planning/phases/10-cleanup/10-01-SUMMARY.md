---
phase: 10-cleanup
plan: 01
subsystem: cleanup
tags: [mqtt, scheduler, jwt, session, lux-removal]

# Dependency graph
requires:
  - phase: 09-esp32-firmware
    provides: Complete codebase with lux code to clean up
provides:
  - "Codebase without any lux-sensor dead code"
  - "90-second token rotation interval"
  - "30-day student JWT sessions"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Token rotation interval configurable via IntervalTrigger(seconds=N)"

key-files:
  created: []
  modified:
    - app/services/mqtt.py
    - app/models/device.py
    - app/templates/admin_devices.html
    - dummy_client/main.py
    - tests/test_mqtt.py
    - tests/test_dummy_client.py
    - app/services/scheduler.py
    - app/routers/auth.py

key-decisions:
  - "90s token rotation balances MQTT churn reduction with reasonable check-in freshness"
  - "30-day student sessions avoid repeated logins across browser restarts on school devices"

patterns-established:
  - "Token rotation interval set in seconds for fine-grained control"

requirements-completed: [CLN-01, CLN-02, CLN-03]

# Metrics
duration: 4min
completed: 2026-04-08
---

# Phase 10 Plan 01: Cleanup Summary

**Removed all lux-sensor dead code, tuned token rotation to 90s, extended student sessions to 30 days**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-08T07:06:58Z
- **Completed:** 2026-04-08T07:10:34Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Removed all lux-related code from MQTT handlers, device model, admin template, dummy client, and tests (zero lux references remain)
- Changed token issuance interval from 60s to 90s to reduce unnecessary MQTT churn
- Extended student JWT and cookie expiry from 1 hour to 30 days for persistent login

## Task Commits

Each task was committed atomically:

1. **Task 1: Remove all lux-related code** - `9b0df57` (refactor)
2. **Task 2: Tune token rotation to 90s and student session to 30 days** - `705595e` (feat)

## Files Created/Modified
- `app/services/mqtt.py` - Removed lux subscription, handler branch, and _handle_lux function
- `app/models/device.py` - Removed last_lux column and Float import
- `app/templates/admin_devices.html` - Removed Lux column header and data cell
- `dummy_client/main.py` - Removed LUX_VALUE, lux_loop function, lux thread
- `tests/test_mqtt.py` - Removed lux subscription assertion and test_lux_update test
- `tests/test_dummy_client.py` - Removed LUX_VALUE config test and TestLux class
- `app/services/scheduler.py` - Changed IntervalTrigger from minutes=1 to seconds=90
- `app/routers/auth.py` - Changed student expires from timedelta(hours=1) to timedelta(days=30)

## Decisions Made
- 90s token rotation chosen as balance between MQTT churn reduction and check-in URL freshness
- 30-day student sessions match typical school term length, reducing login friction

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing test failure in test_teacher.py::test_csv_export_content (CSV delimiter mismatch: code uses comma, test expects semicolon) - not related to this plan's changes, logged as out-of-scope

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Codebase is cleaner with no dead lux code
- Token and session lifetimes tuned for production UX
- Pre-existing CSV delimiter test failure should be addressed separately

---
*Phase: 10-cleanup*
*Completed: 2026-04-08*
