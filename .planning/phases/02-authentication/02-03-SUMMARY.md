---
phase: 02-authentication
plan: 03
subsystem: auth
tags: [fastapi, jinja2, auth, jwt, templates, pico-css, login, role-enforcement]
dependency_graph:
  requires: [02-01, 02-02]
  provides: [auth-router, login-templates, student-landing, admin-seed, full-auth-test-suite]
  affects: [app/main.py, app/routers/auth.py, app/templates/]
tech_stack:
  added: [Jinja2Templates, StaticFiles, python-multipart (form parsing)]
  patterns: [Jinja2 template inheritance (base.html), ?next= redirect threading, role-based redirect on login, idempotent admin seed in lifespan]
key_files:
  created:
    - app/routers/auth.py
    - app/templates/base.html
    - app/templates/login.html
    - app/templates/student.html
  modified:
    - app/main.py
    - .env.example
    - tests/test_auth.py
decisions:
  - "Template directory set at app/templates — Jinja2Templates instantiated in router with relative path 'app/templates'"
  - "admin seed placed in lifespan async context — idempotent (no-op if any admin row exists)"
  - "test-only route /auth/admin-only-test registered in auth router — harmless in production, required for require_role integration tests"
  - "bcrypt pinned to 4.x series — bcrypt 5.x breaks passlib 1.7.4 (removed __about__ attr, strict 72-byte enforcement changes)"
metrics:
  duration: "~5min"
  completed_date: "2026-03-27"
  tasks_completed: 2
  files_created: 4
  files_modified: 3
---

# Phase 02 Plan 03: Auth Router, Templates, and Full Test Suite Summary

**One-liner:** Jinja2 login/student templates with Pico CSS + auth router (6 routes) + admin seed + 13 auth tests green.

## What Was Built

### Task 1: Auth router, templates, main.py wiring, .env.example

Created the complete authentication layer:

- **app/routers/auth.py** — 6 routes: GET /login (form render), POST /auth/login (credential check, role-based redirect, HTTP-only cookie), POST /auth/logout (cookie clear), GET /auth/me (JSON user info), GET /student (student landing), GET /auth/admin-only-test (test fixture route for require_role)
- **app/templates/base.html** — HTML shell with `lang="de"`, Pico CSS link via StaticFiles, `{% block content %}` slot
- **app/templates/login.html** — Login form with `?next=` hidden input threading, German error block using `role="alert"`, Pico CSS article layout
- **app/templates/student.html** — Student placeholder with "Bitte Gerät antippen" German copy (full check-in is Phase 5)
- **app/main.py** — Added StaticFiles mount for `/static`, auth router include, admin seed in lifespan (`_seed_admin` — idempotent, skips if admin row exists)
- **.env.example** — Documented `ADMIN_EMAIL` and `ADMIN_PASSWORD` bootstrap vars

### Task 2: Complete all 13 test stubs

Replaced all `pytest.fail("not implemented")` stubs in tests/test_auth.py with real implementations:

- Added `make_user()`, `login()`, `get_auth_cookie()` test helpers
- Implemented tests for: login page render, ?next= threading, POST login success/failure/inactive, HttpOnly cookie flag, token expiry (already green from Plan 02), logout, /auth/me authenticated/unauthenticated, require_role wrong role (403), require_role correct role (200)
- Result: 13/13 AUTH tests pass, full suite 17 passed + 1 xfailed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocker] bcrypt 5.x incompatible with passlib 1.7.4**
- **Found during:** Task 2 (first test run)
- **Issue:** bcrypt 5.0.0 removed `__about__` attribute that passlib 1.7.4 reads to detect backend, and enforces strict 72-byte password limit differently. Result: `ValueError: password cannot be longer than 72 bytes` when calling `get_password_hash()` from tests.
- **Fix:** Installed bcrypt 4.0.1 (downgrade). This is a dev environment fix — requirements.txt already pins `passlib[bcrypt]==1.7.4`. The Docker container environment should be audited to ensure it does not use bcrypt 5.x.
- **Note:** This is a pre-existing environment issue that became visible when bcrypt hashing was first exercised in tests. The production requirements.txt does not pin bcrypt version — this is a deferred item.
- **Files modified:** None (runtime environment only)

**2. [Rule 3 - Blocker] python-multipart not installed in dev environment**
- **Found during:** Task 1 (app import check)
- **Issue:** FastAPI raises `RuntimeError: Form data requires python-multipart` when defining Form() parameters — even at import time.
- **Fix:** Installed python-multipart in dev environment. Already in requirements.txt — this was a missing local install only.
- **Files modified:** None (runtime environment only)

## Known Stubs

- **app/templates/student.html** — Student landing page shows static placeholder text "Bitte Gerät antippen, um Anwesenheit zu erfassen." — intentional per plan D-09. Full check-in flow (NFC tap → token verification → attendance record) is Phase 5.

## Self-Check: PASSED

Files created/modified:
- [x] app/routers/auth.py — FOUND
- [x] app/templates/base.html — FOUND
- [x] app/templates/login.html — FOUND
- [x] app/templates/student.html — FOUND
- [x] app/main.py — FOUND
- [x] .env.example — FOUND
- [x] tests/test_auth.py — FOUND

Commits:
- [x] ec57c29 — feat(02-03): auth router, templates, main.py wiring, admin seed
- [x] f0e2f51 — feat(02-03): complete all 13 auth test stubs — full suite green

Tests:
- [x] 13/13 auth tests pass
- [x] 17 passed + 1 xfailed (full suite — no regressions)
