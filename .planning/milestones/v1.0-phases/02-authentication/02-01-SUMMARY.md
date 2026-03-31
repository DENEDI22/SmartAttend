---
phase: 02-authentication
plan: 01
subsystem: testing
tags: [test-scaffold, fixtures, pico-css, wave-0]
dependency_graph:
  requires: []
  provides: [test-auth-stubs, conftest-auth-fixtures, pico-css-static]
  affects: [02-02-PLAN, 02-03-PLAN]
tech_stack:
  added: []
  patterns: [pytest-fixtures, testclient-dependency-override, in-memory-sqlite-testing]
key_files:
  created:
    - tests/test_auth.py
    - app/static/pico.min.css
  modified:
    - tests/conftest.py
decisions:
  - "Patch module-level engine in db_session fixture to prevent lifespan create_all hitting production DB path"
  - "test_client uses follow_redirects=False to allow auth tests to inspect 303 redirects"
metrics:
  duration: 136s
  completed: 2026-03-27
  tasks_completed: 2
  files_modified: 3
requirements:
  - AUTH-01
  - AUTH-02
  - AUTH-03
  - AUTH-04
  - AUTH-05
  - AUTH-06
  - AUTH-07
---

# Phase 02 Plan 01: Test Scaffold and Static Assets Summary

Wave 0 scaffold complete: 13 failing test stubs, auth fixtures in conftest.py, and Pico CSS v2 committed as static asset.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Extend conftest.py with auth fixtures | c502053 | tests/conftest.py |
| 2 | Create test_auth.py stubs and download Pico CSS | 4b326bb | tests/test_auth.py, app/static/pico.min.css, tests/conftest.py |

## Verification Results

```
python3 -m pytest tests/test_auth.py -q
# 13 failed in 0.20s (all FAILED, no ERRORs)

python3 -m pytest tests/ -q
# 13 failed, 4 passed, 1 xfailed in 0.59s

wc -c app/static/pico.min.css
# 83319 (83KB — well above 10KB minimum)
```

## Decisions Made

1. **Module-level engine patching**: The `app/main.py` lifespan runs `Base.metadata.create_all(bind=engine)` at TestClient startup. The module-level `engine` in `app.database` is created at import time from the settings, which resolves to the production DB path when no `.env` exists. The `db_session` fixture uses `monkeypatch.setattr` to replace both `app.database.engine` and `app.main.engine` with the in-memory test engine before TestClient starts, preventing the production DB path from being used.

2. **`follow_redirects=False` in TestClient**: Required so auth tests can inspect 303 redirect responses directly rather than having the client auto-follow them.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Module-level engine causes lifespan failure in tests**
- **Found during:** Task 2 verification
- **Issue:** `TestClient(app, follow_redirects=False)` triggers the FastAPI lifespan which calls `Base.metadata.create_all(bind=engine)`. The `engine` was created at import time pointing to `/app/data/smartattend.db` (non-existent in test env), causing `sqlite3.OperationalError: unable to open database file`.
- **Fix:** Added `monkeypatch.setattr(_app_database, "engine", test_engine)` and `monkeypatch.setattr(_app_main, "engine", test_engine)` in `db_session` fixture to substitute the in-memory engine before lifespan runs.
- **Files modified:** tests/conftest.py
- **Commit:** 4b326bb

## Known Stubs

All 13 test functions in `tests/test_auth.py` call `pytest.fail("not implemented")` — intentional stubs for Wave 0. Plans 02-02 and 02-03 will implement the actual test bodies.

## Self-Check: PASSED

- tests/test_auth.py: FOUND
- app/static/pico.min.css: FOUND
- tests/conftest.py: FOUND
- Commit c502053: FOUND
- Commit 4b326bb: FOUND
