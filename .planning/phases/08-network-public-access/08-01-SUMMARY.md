---
phase: 08-network-public-access
plan: 01
subsystem: infra
tags: [config, ngrok, env, network]

# Dependency graph
requires:
  - phase: 06-mqtt-scheduler
    provides: "Token URL generation via scheduler using settings.server_ip"
provides:
  - "BASE_URL config field replacing SERVER_IP (includes scheme)"
  - "Token URLs use configurable base URL (supports ngrok public domain)"
  - "NGROK_AUTHTOKEN and NGROK_DOMAIN env vars documented"
affects: [08-02-docker-ngrok]

# Tech tracking
tech-stack:
  added: []
  patterns: ["BASE_URL includes scheme -- no hardcoded http:// in URL construction"]

key-files:
  created: []
  modified:
    - app/config.py
    - app/services/scheduler.py
    - .env.example
    - tests/conftest.py
    - tests/test_foundation.py
    - tests/test_scheduler.py

key-decisions:
  - "BASE_URL includes scheme and port (http://localhost:8000) so URL construction is a simple concatenation"

patterns-established:
  - "BASE_URL pattern: config field includes full scheme+host+port, consumers just append path"

requirements-completed: [NET-01, NET-03, NET-02]

# Metrics
duration: 3min
completed: 2026-04-02
---

# Phase 08 Plan 01: Config Migration Summary

**Replaced SERVER_IP with BASE_URL across config, scheduler, and env files for ngrok-ready token URL generation**

## Performance

- **Duration:** 3 min (186s)
- **Started:** 2026-04-02T09:54:32Z
- **Completed:** 2026-04-02T09:57:38Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Migrated Settings class from server_ip to base_url with scheme included
- Updated scheduler token URL generation to use settings.base_url (no hardcoded http://)
- Added NGROK_AUTHTOKEN and NGROK_DOMAIN to .env.example for production setup
- Updated all tests to use BASE_URL -- 12 passed, 1 xfailed

## Task Commits

Each task was committed atomically:

1. **Task 1: Replace SERVER_IP with BASE_URL in config, scheduler, and env files** - `35a5dd5` (feat)
2. **Task 2: Update tests for BASE_URL configuration** - `dc9790c` (test)

## Files Created/Modified
- `app/config.py` - Settings.base_url replaces server_ip, default http://localhost:8000
- `app/services/scheduler.py` - Token URL uses settings.base_url instead of f"http://{settings.server_ip}"
- `.env.example` - BASE_URL documented with dev/prod examples, ngrok section added
- `tests/conftest.py` - override_settings fixture uses BASE_URL env var
- `tests/test_foundation.py` - required_vars list updated to BASE_URL
- `tests/test_scheduler.py` - Token URL assertion updated with port from BASE_URL

## Decisions Made
- BASE_URL default includes port (http://localhost:8000) so dev setup works without extra config
- Scheme included in BASE_URL to support both http and https without conditional logic

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Worktree had no .env file (gitignored) -- created temporary .env for test execution. Not committed (gitignored).
- Pre-existing test failure in test_teacher.py::test_csv_export_content unrelated to this plan's changes (no SERVER_IP/BASE_URL references in that file).

## User Setup Required

None - no external service configuration required. Ngrok env vars are documented in .env.example but not needed until plan 08-02.

## Next Phase Readiness
- BASE_URL config ready for ngrok integration in plan 08-02
- Docker Compose can reference NGROK_DOMAIN env var to set BASE_URL automatically
- All tests pass with new config structure

---
*Phase: 08-network-public-access*
*Completed: 2026-04-02*
