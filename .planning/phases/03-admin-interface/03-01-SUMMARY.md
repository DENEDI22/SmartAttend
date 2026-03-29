---
phase: 03-admin-interface
plan: 01
subsystem: ui
tags: [fastapi, jinja2, pico-css, admin, vanilla-js, sqlalchemy]

requires:
  - phase: 02-authentication
    provides: JWT auth, require_role dependency, base.html template, auth router
provides:
  - SchoolClass ORM model
  - Admin router skeleton with /admin, /admin/devices, /admin/users
  - Admin base template with shared nav
  - admin.js vanilla JS for inline-edit and conflict-check
  - Test scaffold with 10 ADMIN requirement stubs
  - admin_client, seed_device, seed_teacher, seed_school_class fixtures
affects: [03-02-devices, 03-03-users, 03-04-schedule]

tech-stack:
  added: []
  patterns: [admin_base.html extends base.html with nav, admin.js inline-edit via data-original attributes]

key-files:
  created:
    - app/models/school_class.py
    - app/routers/admin.py
    - app/templates/admin_base.html
    - app/templates/admin_devices.html
    - app/templates/admin_users.html
    - app/static/admin.js
    - tests/test_admin.py
  modified:
    - app/models/__init__.py
    - app/templates/base.html
    - app/main.py
    - tests/conftest.py

key-decisions:
  - "db_session.refresh() required after commit in test fixtures to ensure SQLite in-memory session visibility for endpoint queries"
  - "admin_base.html uses Pico CSS nav with aria-current for active page indication"

patterns-established:
  - "Admin templates extend admin_base.html which extends base.html — two-level template inheritance"
  - "admin.js uses data-original attributes on inputs for change detection"
  - "admin_client fixture: create admin user, refresh, login, return authenticated test_client"

requirements-completed: [ADMIN-01, ADMIN-02, ADMIN-03, ADMIN-04, ADMIN-05, ADMIN-06, ADMIN-07, ADMIN-08, ADMIN-09, ADMIN-10]

duration: 9min
completed: 2026-03-29
---

# Phase 3 Plan 1: Admin Foundation Summary

**SchoolClass model, admin router skeleton with nav, admin.js inline-edit JS, and 10 ADMIN test stubs with shared fixtures**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-29T21:24:51Z
- **Completed:** 2026-03-29T21:34:15Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- SchoolClass model registered and creates table via SQLAlchemy metadata
- Admin router skeleton serves /admin (303 redirect), /admin/devices, /admin/users with role enforcement
- Admin base template with shared nav (Geraete, Benutzer, Abmelden) and flash message support
- admin.js provides inline-edit change detection and schedule conflict-check logic
- 10 test stubs for ADMIN-01 through ADMIN-10, plus 5 passing infrastructure tests
- Shared fixtures: admin_client, seed_device, seed_teacher, seed_school_class

## Task Commits

Each task was committed atomically:

1. **Task 1: SchoolClass model + admin router + templates + admin.js** - `faa7c5b` (feat)
2. **Task 2: Test scaffold -- 10 stubs + admin auth helper fixtures** - `36ca6f1` (feat)

## Files Created/Modified
- `app/models/school_class.py` - SchoolClass ORM model with unique name
- `app/routers/admin.py` - Admin router skeleton with redirect and placeholder pages
- `app/templates/admin_base.html` - Admin base template with shared nav and flash messages
- `app/templates/admin_devices.html` - Device management placeholder template
- `app/templates/admin_users.html` - User management placeholder template
- `app/static/admin.js` - Vanilla JS for inline-edit change detection and conflict-check
- `app/models/__init__.py` - Added SchoolClass import and __all__ entry
- `app/templates/base.html` - Added head_extra block for script injection
- `app/main.py` - Registered admin router
- `tests/test_admin.py` - 10 ADMIN requirement stubs + 5 infrastructure tests
- `tests/conftest.py` - admin_client, seed_device, seed_teacher, seed_school_class fixtures

## Decisions Made
- Added `db_session.refresh()` after commit in admin_client fixture to ensure SQLite in-memory session visibility when endpoint queries run through the shared session
- Used Pico CSS nav with aria-current="page" for active page indication in admin_base.html

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] SQLite session visibility after commit in test fixtures**
- **Found during:** Task 2 (Test scaffold)
- **Issue:** admin_client fixture login POST returned 200 (invalid credentials) despite user being committed to db_session. SQLAlchemy session state after commit() not visible to endpoint queries through same session without intervening refresh/query.
- **Fix:** Added `db_session.refresh(admin)` after `db_session.commit()` in admin_client fixture, and `db_session.refresh(teacher)` in test_admin_requires_admin_role test.
- **Files modified:** tests/conftest.py, tests/test_admin.py
- **Verification:** All 15 tests pass (5 passed, 10 skipped)
- **Committed in:** 36ca6f1 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential fix for test correctness. No scope creep.

## Issues Encountered
None beyond the auto-fixed session visibility issue.

## Known Stubs
- `app/templates/admin_devices.html` - Placeholder "Keine Geraete registriert." — replaced by Plan 02
- `app/templates/admin_users.html` - Placeholder "Keine Benutzer vorhanden." — replaced by Plan 03
- `app/routers/admin.py` devices_page returns empty devices list — Plan 02 wires real data
- `app/routers/admin.py` users_page returns empty users/school_classes lists — Plan 03 wires real data

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Admin router skeleton ready for Wave 2 plans to add device management (Plan 02) and user management (Plan 03) in parallel
- SchoolClass model available for user creation forms
- admin.js ready for inline-edit forms in device and user pages
- Test fixtures available for all Wave 2 tests

---
*Phase: 03-admin-interface*
*Completed: 2026-03-29*
