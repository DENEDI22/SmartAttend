---
phase: 11-password-management
plan: 01
subsystem: auth
tags: [password, bcrypt, fastapi, jinja2, pico-css]

# Dependency graph
requires:
  - phase: 02-authentication
    provides: JWT auth, verify_password, get_password_hash, get_current_user
provides:
  - POST /auth/password endpoint for self-service password change
  - Reusable _password_change.html partial template
  - Password change form on all 3 role dashboards
affects: [12-admin-password-reset]

# Tech tracking
tech-stack:
  added: []
  patterns: [role-based redirect with query param messaging, reusable Jinja2 partial includes]

key-files:
  created: [app/templates/_password_change.html, tests/test_password.py]
  modified: [app/routers/auth.py, app/templates/student.html, app/templates/teacher_dashboard.html, app/templates/admin_base.html, app/templates/student_base.html, app/config.py]

key-decisions:
  - "Validation order: length check first, then match check, then current password verify"
  - "German error messages via URL query params matching existing msg/error pattern"

patterns-established:
  - "Password change partial: reusable _password_change.html included via Jinja2 {% include %}"
  - "Role-based redirect mapping: dict lookup for admin/teacher/student base URLs"

requirements-completed: [PWD-01]

# Metrics
duration: 4min
completed: 2026-04-08
---

# Phase 11 Plan 01: Password Change Summary

**Self-service password change for all roles with validation, German error messages, and reusable form partial on all dashboards**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-08T07:26:44Z
- **Completed:** 2026-04-08T07:30:26Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 8

## Accomplishments
- POST /auth/password endpoint handling password change with 3 validation checks
- Reusable _password_change.html partial included in student, teacher, and admin dashboards
- 9 tests covering happy path, validation errors, unauthenticated access, and multi-role usage

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests for password change** - `162282b` (test)
2. **Task 1 GREEN: Implement password change endpoint and templates** - `11cdd2a` (feat)

_TDD task with RED and GREEN commits._

## Files Created/Modified
- `app/routers/auth.py` - Added POST /auth/password endpoint with validation
- `app/templates/_password_change.html` - Reusable password change form partial
- `app/templates/student.html` - Includes password change partial
- `app/templates/teacher_dashboard.html` - Includes password change partial
- `app/templates/admin_base.html` - Includes password change partial
- `app/templates/student_base.html` - Added msg/error query param display
- `app/config.py` - Added extra="ignore" to Settings for ngrok env vars
- `tests/test_password.py` - 9 test cases for password change

## Decisions Made
- Validation order: length >= 8 first, then confirm match, then current password verify -- fail fast on cheap checks
- German error messages encoded in URL query params, matching existing admin/teacher msg/error pattern

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Settings extra="ignore" for ngrok env vars**
- **Found during:** Task 1 RED phase
- **Issue:** .env file contains ngrok_authtoken and ngrok_domain which are not in Settings model, causing pydantic ValidationError and blocking ALL tests
- **Fix:** Added `extra="ignore"` to SettingsConfigDict in app/config.py
- **Files modified:** app/config.py
- **Verification:** All tests can now load without ValidationError
- **Committed in:** 162282b (RED commit)

**2. [Rule 2 - Missing Critical] Added msg/error display to student_base.html**
- **Found during:** Task 1 GREEN phase
- **Issue:** student_base.html lacked msg/error query param display that teacher_base.html and admin_base.html already have -- password change success/error messages would be invisible to students
- **Fix:** Added msg/error alert paragraphs to student_base.html matching existing pattern
- **Files modified:** app/templates/student_base.html
- **Verification:** Student password change redirects now show success/error messages
- **Committed in:** 11cdd2a (GREEN commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 missing critical)
**Impact on plan:** Both fixes necessary for tests to run and for feature to work correctly for students. No scope creep.

## Issues Encountered
- Pre-existing test failure in test_teacher.py::test_csv_export_content (expects semicolons but CSV uses commas) -- unrelated to this plan, not fixed

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Password change infrastructure in place
- Admin password reset (plan 02) can build on same verify_password/get_password_hash imports
- All role dashboards have the partial include pattern established

---
*Phase: 11-password-management*
*Completed: 2026-04-08*
