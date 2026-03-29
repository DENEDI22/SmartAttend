---
phase: 03-admin-interface
plan: 02
subsystem: ui
tags: [fastapi, jinja2, pico-css, device-management, inline-editing, sqlalchemy]

# Dependency graph
requires:
  - phase: 02-authentication
    provides: auth dependencies (require_role, get_current_user), login/logout endpoints
  - phase: 01-foundation
    provides: Device model, Base template, database engine, SQLAlchemy patterns
provides:
  - Device management page at /admin/devices with inline-editable table
  - Bulk room/label update endpoint (POST /admin/devices/update)
  - Per-device enable/disable toggle endpoint (POST /admin/devices/{id}/toggle)
  - Admin router skeleton with redirect, device and user page stubs
  - Admin base template with shared nav (Geraete, Benutzer, Abmelden)
  - admin.js with inline-edit change detection and dynamic form submission
  - SchoolClass model for class name management
  - Test fixtures: admin_client, seed_device, seed_teacher, seed_school_class
  - 3 passing ADMIN tests (ADMIN-01, ADMIN-02, ADMIN-03)
affects: [03-admin-interface, 04-teacher-interface]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "div#edit-form with JS dynamic form submission to avoid nested HTML forms"
    - "Per-row toggle form in table Aktionen column"
    - "admin_base.html extends base.html with nav and flash message support"
    - "admin_client fixture: create user, refresh, login, return test_client"

key-files:
  created:
    - app/routers/admin.py
    - app/templates/admin_devices.html
    - app/templates/admin_base.html
    - app/templates/admin_users.html
    - app/static/admin.js
    - app/models/school_class.py
    - tests/test_admin.py
  modified:
    - app/models/__init__.py
    - app/templates/base.html
    - app/main.py
    - tests/conftest.py

key-decisions:
  - "Use div#edit-form instead of form element to avoid nested form issue with toggle buttons"
  - "Read is_enabled before db.commit() in toggle endpoint to avoid ObjectDeletedError"
  - "db_session.refresh(admin) required in admin_client fixture for session sync after commit"

patterns-established:
  - "Admin page pattern: extends admin_base.html, sets active_page context var for nav highlighting"
  - "Inline edit pattern: data-original attributes + JS change detection + dynamic form submission"
  - "Toggle pattern: separate form per row in Aktionen column with outline button"

requirements-completed: [ADMIN-01, ADMIN-02, ADMIN-03]

# Metrics
duration: 12min
completed: 2026-03-29
---

# Phase 3 Plan 02: Device Management Summary

**Device management page with inline-editable room/label table, per-row enable/disable toggle, and bulk save via JS dynamic form submission**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-29T21:36:58Z
- **Completed:** 2026-03-29T21:49:17Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments
- Device table renders all 7 columns: device_id, room, label, online/offline status, enabled/disabled, last_seen, lux
- Room and label fields are inline-editable with save/reset buttons (disabled until changes detected)
- Enable/disable toggle works per-row via separate POST forms
- Empty state shown when no devices registered
- 3 ADMIN test stubs replaced with real passing tests (ADMIN-01, ADMIN-02, ADMIN-03)
- Full admin infrastructure created (router, templates, JS, SchoolClass model, fixtures)

## Task Commits

Each task was committed atomically:

1. **Task 1: Device management routes + template with inline editing** - `70b94fc` (feat)
2. **Task 2: Implement device test cases (ADMIN-01, ADMIN-02, ADMIN-03)** - `b882b71` (feat)

## Files Created/Modified
- `app/routers/admin.py` - Admin router with device CRUD endpoints and user page stub
- `app/templates/admin_devices.html` - Device management page with inline-editable table
- `app/templates/admin_base.html` - Admin base template with shared nav and flash messages
- `app/templates/admin_users.html` - User management placeholder page
- `app/static/admin.js` - Inline edit change detection, dynamic form submission, schedule conflict check stub
- `app/models/school_class.py` - SchoolClass ORM model (id, name)
- `app/models/__init__.py` - Added SchoolClass import
- `app/templates/base.html` - Added head_extra block for page-specific scripts
- `app/main.py` - Wired admin router
- `tests/test_admin.py` - 15 tests (8 passing, 7 skipped stubs)
- `tests/conftest.py` - Added admin_client, seed_device, seed_teacher, seed_school_class fixtures

## Decisions Made
- Used `<div id="edit-form">` instead of `<form>` to avoid HTML nested form issue with per-row toggle buttons. JS dynamically creates and submits a form on save button click.
- Read `device.is_enabled` before `db.commit()` in toggle endpoint to avoid SQLAlchemy ObjectDeletedError when accessing expired attribute after commit.
- Added `db_session.refresh(admin)` in admin_client fixture to synchronize session state after commit, preventing intermittent login failures in tests.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed ObjectDeletedError in device toggle endpoint**
- **Found during:** Task 2 (test_toggle_device_enabled)
- **Issue:** After `db.commit()`, accessing `device.is_enabled` triggered ObjectDeletedError because SQLAlchemy expired the instance
- **Fix:** Read `new_status = device.is_enabled` before `db.commit()`, use `new_status` for redirect message
- **Files modified:** app/routers/admin.py
- **Verification:** test_toggle_device_enabled passes consistently
- **Committed in:** b882b71 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed admin_client fixture session sync issue**
- **Found during:** Task 2 (admin_client fixture setup)
- **Issue:** Login returned 200 (failure) intermittently because db_session had stale state after commit
- **Fix:** Added `db_session.refresh(admin)` after commit to force session reload
- **Files modified:** tests/conftest.py
- **Verification:** admin_client fixture passes consistently across multiple runs
- **Committed in:** b882b71 (Task 2 commit)

**3. [Rule 3 - Blocking] Created Plan 03-01 prerequisite files**
- **Found during:** Task 1 (execution start)
- **Issue:** Plan 03-02 depends on Plan 03-01 (wave 1) which creates admin router skeleton, templates, JS, SchoolClass model. These files did not exist yet.
- **Fix:** Created all prerequisite files as part of Task 1 following Plan 03-01 specification
- **Files modified:** All created files listed above
- **Verification:** All tests pass, infrastructure functional
- **Committed in:** 70b94fc (Task 1 commit)

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 blocking)
**Impact on plan:** All auto-fixes necessary for correctness. Plan 03-01 prerequisites were essential for execution.

## Issues Encountered
- SQLAlchemy shared session between test fixture and request handler causes ObjectDeletedError after commit -- resolved by reading values before commit
- Admin client fixture login fails without explicit session refresh after commit -- SQLAlchemy in-memory SQLite session sync requires explicit refresh

## Known Stubs
None -- all device management functionality is fully wired and functional.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Device management page fully functional with all CRUD operations
- 7 test stubs remain for Plans 03 (users) and 04 (schedule): ADMIN-04 through ADMIN-10
- Admin base template and JS infrastructure ready for user management page

---
*Phase: 03-admin-interface*
*Completed: 2026-03-29*
