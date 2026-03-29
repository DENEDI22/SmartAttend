---
phase: 03-admin-interface
plan: 04
subsystem: admin
tags: [schedule, crud, overlap-detection, details-element, pico-css]

requires:
  - phase: 03-admin-interface-02
    provides: "Device management routes, admin_devices.html template, admin.js"
  - phase: 01-foundation
    provides: "ScheduleEntry model, SchoolClass model, Device model"
provides:
  - "Schedule CRUD: add, delete, view per device"
  - "Overlap detection (server-side + JSON API for JS)"
  - "Expandable per-device schedule sections with <details>"
  - "Conflict-check API at GET /admin/api/schedule/check-conflict"
affects: [04-teacher-interface, 06-mqtt-scheduler]

tech-stack:
  added: []
  patterns:
    - "Half-open interval overlap check: s1 < e2 AND s2 < e1"
    - "querySelectorAll for multiple per-device conflict-check forms"
    - "StaticPool for in-memory SQLite test engine (prevents connection loss after commit)"

key-files:
  created: []
  modified:
    - app/routers/admin.py
    - app/templates/admin_devices.html
    - app/static/admin.js
    - tests/test_admin.py
    - tests/conftest.py

key-decisions:
  - "StaticPool required for in-memory SQLite test engine to prevent db.get() returning None after commit in async route handlers"
  - "Half-open interval [start, end) for overlap detection -- adjacent entries (end==start) are allowed"
  - "German UI text for conflict messages (Zeitkonflikt)"

patterns-established:
  - "StaticPool in conftest for in-memory SQLite: prevents async connection loss"
  - "Half-open interval overlap: ScheduleEntry.start_time < end_time AND ScheduleEntry.end_time > start_time"

requirements-completed: [ADMIN-07, ADMIN-08, ADMIN-09, ADMIN-10]

duration: 14min
completed: 2026-03-30
---

# Phase 03 Plan 04: Schedule Management Summary

**Schedule CRUD with per-device expandable sections, half-open interval overlap detection, and JSON conflict-check API for JS validation**

## Performance

- **Duration:** 14 min
- **Started:** 2026-03-29T21:53:35Z
- **Completed:** 2026-03-30T22:07:23Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Schedule entries visible per device in expandable `<details>` sections (ADMIN-07)
- Add schedule entry with class, teacher, weekday, time fields + auto-create SchoolClass (ADMIN-08)
- Overlap detection rejects conflicting entries server-side and via JSON API (ADMIN-09, D-17)
- Delete schedule entry with confirmation (ADMIN-10)
- All 19 admin tests pass, full suite green (36 passed, 0 skipped)

## Task Commits

Each task was committed atomically:

1. **Task 1: Schedule CRUD routes + conflict check API + device page schedule sections** - `7bafc25` (feat)
2. **Task 2: Implement schedule test cases (ADMIN-07/08/09/10)** - `70c2fcc` (feat)

## Files Created/Modified
- `app/routers/admin.py` - Added check_schedule_conflict helper, schedule_add, schedule_delete, api_check_conflict routes; updated devices_page to load schedule data
- `app/templates/admin_devices.html` - Added expandable `<details>` sections per device with schedule table and add-entry form
- `app/static/admin.js` - Changed conflict check from querySelector to querySelectorAll for multiple per-device forms
- `tests/test_admin.py` - Replaced 4 skipped stubs with real tests, added 2 additional tests (conflict API, adjacent entries edge case)
- `tests/conftest.py` - Added StaticPool import and poolclass=StaticPool to test engine

## Decisions Made
- Used StaticPool for in-memory SQLite test engine -- without it, db.get() returns None after commit when called from async route handlers (connection pool gives different connection to empty in-memory DB)
- Half-open interval overlap check [start, end) allows adjacent entries (end_time of one == start_time of next)
- Auto-create SchoolClass on schedule entry add (consistent with D-14 pattern from user creation)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed in-memory SQLite connection pooling in test conftest**
- **Found during:** Task 2 (schedule test implementation)
- **Issue:** db.get(User, id) returned None in async route handlers after db_session.commit() because default pool gave different connections to the in-memory SQLite DB
- **Fix:** Added poolclass=StaticPool to test engine creation in conftest.py
- **Files modified:** tests/conftest.py
- **Verification:** All 19 admin tests pass, including schedule tests that commit before GET requests
- **Committed in:** 70c2fcc (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Essential fix for test reliability. Without StaticPool, any test that commits data then makes an authenticated request would fail.

## Issues Encountered
- In-memory SQLite without StaticPool causes connection isolation: after Session.commit() expires objects, re-loading them opens a new connection that sees an empty database. This affected all schedule tests that add data then verify via HTTP requests. Root cause identified and fixed with StaticPool.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 10 ADMIN requirements (ADMIN-01 through ADMIN-10) now have passing tests
- Admin interface complete: device management, user management, schedule management
- Ready for Phase 04 (teacher interface) which will consume schedule data

## Known Stubs
None - all schedule functionality is fully wired with real data.

---
*Phase: 03-admin-interface*
*Completed: 2026-03-30*
