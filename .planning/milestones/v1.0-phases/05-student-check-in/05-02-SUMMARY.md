---
phase: 05-student-check-in
plan: 02
subsystem: check-in, api
tags: [fastapi, sqlalchemy, jwt, check-in, attendance]

requires:
  - phase: 05-student-check-in
    plan: 01
    provides: "Test fixtures, checkin.html template, conftest seed data"
  - phase: 02-authentication
    provides: "Auth middleware, JWT cookies, require_role dependency"

provides:
  - "GET /checkin endpoint with manual auth, token validation, room/time display"
  - "POST /checkin endpoint with attendance record creation"
  - "Complete student check-in flow: NFC URL to attendance record"

affects:
  - app/main.py: "Added checkin_router include"
  - app/routers/checkin.py: "New file"
  - tests/test_checkin.py: "Replaced 11 stubs with real assertions"

tech-stack:
  added: []
  patterns:
    - "Manual auth check via _get_user_from_cookie (returns None, no redirect)"
    - "Token validation helper _validate_token returns (token, error) tuple"
    - "IntegrityError safety net for duplicate check-in race condition"

key-files:
  created:
    - app/routers/checkin.py
  modified:
    - app/main.py
    - tests/test_checkin.py

key-decisions:
  - "Manual auth check on GET /checkin to preserve token query param in redirect"
  - "IntegrityError catch as safety net for concurrent duplicate check-ins"

metrics:
  duration: 163s
  tasks_completed: 2
  tasks_total: 2
  test_count: 11
  test_pass: 11
  files_created: 1
  files_modified: 2
  completed: "2026-03-30T00:36:09Z"
---

# Phase 5 Plan 2: Check-in Router Implementation Summary

Complete student check-in flow with GET/POST /checkin endpoints, token validation, German error messages, and 11 passing tests.

## What Was Built

### Check-in Router (`app/routers/checkin.py`)
- **GET /checkin**: Manual auth check (returns None instead of raising), token validation, room/time display from Device+ScheduleEntry, duplicate detection showing original check-in time
- **POST /checkin**: Uses `require_role("student")`, validates token, creates AttendanceRecord, IntegrityError safety net for race conditions
- **Helper `_get_user_from_cookie`**: Mirrors `get_current_user` but returns None -- avoids losing token query param on redirect
- **Helper `_validate_token`**: Returns (token, error) tuple covering invalid, missing, expired, inactive cases
- **German error messages**: "Ungültiger oder fehlender Token", "Diese Stunde ist bereits beendet", "Dieser Token ist nicht mehr gültig", "Nur Schüler können sich einchecken", "Sie haben sich bereits eingecheckt"

### Router Wiring (`app/main.py`)
- Added `checkin_router` include after existing admin router

### Tests (`tests/test_checkin.py`)
All 11 test stubs replaced with real assertions:
1. `test_checkin_page_shows_lesson_info` -- room R101, times 08:00/09:30
2. `test_checkin_unauthenticated_redirects_to_login` -- 303 with token in location
3. `test_checkin_post_validates_token` -- 200 with "erfolgreich"
4. `test_checkin_duplicate_rejected` -- "bereits" in response
5. `test_checkin_success_writes_record` -- DB query confirms AttendanceRecord
6. `test_checkin_expired_token_error` -- "Diese Stunde ist bereits beendet"
7. `test_checkin_invalid_token_error` -- "fehlender Token"
8. `test_checkin_missing_token_error` -- "fehlender Token"
9. `test_checkin_inactive_token_error` -- "nicht mehr"
10. `test_checkin_non_student_rejected` -- "Nur Sch"
11. `test_checkin_already_checked_in_shows_time` -- "Eingecheckt um"

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 723d59c | feat(05-02): implement checkin router with GET/POST endpoints and wire into main.py |
| 2 | ffe9854 | test(05-02): implement all 11 check-in tests with real assertions |

## Verification

- 11/11 check-in tests pass
- Full test suite: 56 passed, 1 xfailed, 0 failures
- No regressions in auth, admin, teacher, or foundation tests

## Deviations from Plan

None -- plan executed exactly as written.

## Known Stubs

None -- all endpoints are fully functional with real database operations.
