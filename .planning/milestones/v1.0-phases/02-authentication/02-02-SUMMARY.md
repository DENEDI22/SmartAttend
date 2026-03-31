---
phase: 02-authentication
plan: "02"
subsystem: auth
tags: [jwt, bcrypt, passlib, python-jose, fastapi-dependencies, cookie-auth]

# Dependency graph
requires:
  - phase: 02-01
    provides: test fixtures (db_session, test_client), conftest setup, User model in DB
  - phase: 01-foundation
    provides: app/config.py Settings class, app/database.py get_db, app/models/user.py User ORM

provides:
  - app/services/auth.py — verify_password, get_password_hash, create_access_token (HS256 JWT), authenticate_user
  - app/dependencies.py — get_current_user (cookie → User, 303 on bad/missing JWT), require_role (403 on wrong role)
  - app/config.py Settings extended with admin_email and admin_password (both default "")

affects:
  - 02-03  # auth router imports create_access_token, get_current_user, require_role
  - 03-admin  # admin routes use require_role("admin")
  - 04-teacher  # teacher routes use require_role("teacher")
  - 05-student  # student check-in uses get_current_user

# Tech tracking
tech-stack:
  added: [python-jose[cryptography]==3.5.0, passlib[bcrypt]==1.7.4]
  patterns:
    - "ALGORITHM = 'HS256' constant in auth service, imported by dependencies"
    - "CryptContext(schemes=['bcrypt'], deprecated='auto') for timing-safe password ops"
    - "get_current_user reads access_token cookie; 303 redirect to /login for all auth failures"
    - "require_role(*roles) factory returns async dependency; 403 for wrong role"
    - "JWTError catch-all covers ExpiredSignatureError and malformed tokens (Pitfall 5)"

key-files:
  created:
    - app/services/auth.py
    - app/dependencies.py
  modified:
    - app/config.py
    - tests/test_auth.py

key-decisions:
  - "get_current_user raises HTTPException(303) not 401 — browser-friendly redirect for Jinja2 UI"
  - "require_role raises 403 (not redirect) — authenticated but unauthorized user, different UX"
  - "create_access_token takes explicit expires_delta — caller chooses 8h (admin/teacher) vs 1h (student)"
  - "authenticate_user returns None not raises — router decides error presentation"

patterns-established:
  - "Pattern: FastAPI dependency chain — require_role depends on get_current_user"
  - "Pattern: Cookie-based JWT — access_token cookie, Cookie(default=None) parameter"

requirements-completed: [AUTH-02, AUTH-03, AUTH-04, AUTH-05, AUTH-06]

# Metrics
duration: 3min
completed: 2026-03-27
---

# Phase 02 Plan 02: Auth Service and FastAPI Dependencies Summary

**HS256 JWT creation (8h admin/teacher, 1h student) with bcrypt via passlib and FastAPI cookie-based auth dependencies using jose JWTError catch-all for robust redirect behavior**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-27T11:46:40Z
- **Completed:** 2026-03-27T11:48:58Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Created `app/services/auth.py` with bcrypt password hashing, HS256 JWT creation, and safe user lookup
- Created `app/dependencies.py` with `get_current_user` (cookie decode, 303 on any JWT failure) and `require_role` (403 on wrong role)
- Extended `app/config.py` Settings with `admin_email` and `admin_password` bootstrap fields
- Two token expiry tests green: admin (8h) and student (1h) within 10s tolerance

## Task Commits

Each task was committed atomically:

1. **Task 1: Auth service** - `ab06d99` (feat)
2. **Task 2: Config additions + dependencies.py** - `9b69337` (feat)

## Files Created/Modified

- `app/services/auth.py` - verify_password, get_password_hash, create_access_token, authenticate_user, ALGORITHM
- `app/dependencies.py` - get_current_user (cookie-based auth with 303 redirect), require_role factory
- `app/config.py` - Added admin_email and admin_password optional fields (default "")
- `tests/test_auth.py` - Filled in test_token_expiry_admin, test_token_expiry_student; updated test_me_unauthenticated stub with real assertion

## Decisions Made

- `get_current_user` uses 303 redirect (not 401) for all auth failures — appropriate for server-side Jinja2 UI where browsers follow redirects
- `require_role` uses 403 (not redirect) — user is authenticated but lacks permission, different UX than missing auth
- `create_access_token` takes explicit `expires_delta` — keeps role-specific timing logic in the caller (router), not buried in the service

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed missing python-jose and passlib packages**
- **Found during:** Task 1 (auth service tests)
- **Issue:** python-jose and passlib were in requirements.txt but not installed in the system Python environment; tests failed with ModuleNotFoundError
- **Fix:** Ran `pip3 install "python-jose[cryptography]==3.5.0" "passlib[bcrypt]==1.7.4" --break-system-packages`
- **Files modified:** None (system packages)
- **Verification:** Tests passed after installation
- **Committed in:** ab06d99 (Task 1 commit, noted in message)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Dependency installation required for local test execution. Docker environment already has these pinned in requirements.txt.

## Issues Encountered

- `test_me_unauthenticated` remains failing (404 not 303) because `/auth/me` route does not exist until Plan 03 creates the auth router. This is expected behavior per the plan spec.

## Next Phase Readiness

- Plan 03 (auth router) can now import `create_access_token`, `get_current_user`, `require_role` directly
- `authenticate_user` ready for use in POST /auth/login handler
- Admin bootstrap fields in Settings ready for startup seed logic
- All exported symbols verified importable

## Self-Check: PASSED

- FOUND: app/services/auth.py
- FOUND: app/dependencies.py
- FOUND: app/config.py
- FOUND: 02-02-SUMMARY.md
- FOUND: ab06d99 (Task 1 commit)
- FOUND: 9b69337 (Task 2 commit)
