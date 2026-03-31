---
phase: 01-foundation
plan: 02
subsystem: database
tags: [sqlalchemy, sqlite, fastapi, orm, models]

# Dependency graph
requires:
  - phase: 01-foundation plan 01
    provides: app/database.py with Base (DeclarativeBase), engine, SessionLocal, get_db()

provides:
  - 5 SQLAlchemy 2.0-style models with Mapped[] annotations (User, Device, ScheduleEntry, AttendanceToken, AttendanceRecord)
  - app/models/__init__.py that registers all 5 models on Base metadata
  - app/main.py with asynccontextmanager lifespan that calls Base.metadata.create_all()
  - requirements.txt with 10 pinned dependencies for reproducible builds

affects:
  - 01-03 (Docker/Compose needs requirements.txt and main.py as entrypoint)
  - 02-auth (imports User model for JWT auth logic)
  - 03-admin (imports Device, ScheduleEntry, User for admin UI)
  - 04-teacher (imports AttendanceRecord for dashboard)
  - 05-checkin (imports AttendanceToken, AttendanceRecord for check-in flow)
  - 06-mqtt (imports Device, AttendanceToken for MQTT scheduler)

# Tech tracking
tech-stack:
  added:
    - sqlalchemy==2.0.48 (ORM with DeclarativeBase + Mapped[] typed columns)
    - fastapi==0.135.2 (web framework with asynccontextmanager lifespan)
    - uvicorn==0.42.0 (ASGI server)
    - pydantic-settings==2.13.1 (already from Plan 01, now in requirements.txt)
    - jinja2==3.1.6, python-multipart==0.0.22 (template rendering, form parsing)
    - paho-mqtt==2.1.0, apscheduler==3.11.2 (pinned now; used in Phase 6)
    - python-jose==3.5.0, passlib==1.7.4 (pinned now; used in Phase 2)
  patterns:
    - SQLAlchemy 2.0 declarative style with Mapped[] and mapped_column() — NOT legacy Column()
    - FastAPI asynccontextmanager lifespan — NOT deprecated @app.on_event("startup")
    - All models imported in app/models/__init__.py to register on Base metadata before create_all()
    - FK relationships declared with ForeignKey("tablename.id") string references

key-files:
  created:
    - app/models/user.py
    - app/models/device.py
    - app/models/schedule_entry.py
    - app/models/attendance_token.py
    - app/models/attendance_record.py
    - app/main.py
    - requirements.txt
  modified:
    - app/models/__init__.py

key-decisions:
  - "ScheduleEntry has NO subject field — dropped per user decision D-07"
  - "AttendanceRecord has UniqueConstraint on (student_id, token_id) named uq_student_token — prevents duplicate check-ins per D-11"
  - "AttendanceToken has lesson_date (Date) field — specific calendar date per D-09, not derived from schedule"
  - "Device has two independent flags: is_enabled (admin-controlled) and is_online (heartbeat-controlled)"
  - "requirements.txt pins all 10 packages including later-phase dependencies to prevent Docker layer cache invalidation"

patterns-established:
  - "SQLAlchemy 2.0 Mapped[] pattern: all models use class Foo(Base) with Mapped[type] = mapped_column()"
  - "Model registration pattern: app/models/__init__.py must import all models before create_all() is called"
  - "Lifespan pattern: FastAPI app uses asynccontextmanager lifespan, not @app.on_event"
  - "Nullable pattern: Optional fields use Mapped[type | None] = mapped_column(..., nullable=True)"

requirements-completed:
  - FOUND-04

# Metrics
duration: 2min
completed: 2026-03-27
---

# Phase 1 Plan 02: SQLAlchemy Models and FastAPI App Summary

**Five SQLAlchemy 2.0 models (User, Device, ScheduleEntry, AttendanceToken, AttendanceRecord) with FK constraints, plus FastAPI lifespan app and 10-package pinned requirements.txt**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-27T10:29:14Z
- **Completed:** 2026-03-27T10:31:20Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- All 5 SQLAlchemy models created with exact field specs from D-04 through D-11
- AttendanceRecord UniqueConstraint on (student_id, token_id) prevents duplicate check-ins
- ScheduleEntry correctly omits subject field (D-07 decision honored)
- app/main.py uses asynccontextmanager lifespan (not deprecated @app.on_event)
- requirements.txt pins all 10 packages including later-phase dependencies
- test_all_tables_created transitions from xfail to xpassed (functionally green)

## Task Commits

Each task was committed atomically:

1. **Task 1: All 5 SQLAlchemy models** - `2174a93` (feat)
2. **Task 2: main.py and requirements.txt** - `2d0faa8` (feat)

## Files Created/Modified

- `app/models/user.py` - User model: email, first_name, last_name, role, class_name, password_hash, is_active
- `app/models/device.py` - Device model: device_id, room, label, is_enabled, is_online, last_seen, last_lux
- `app/models/schedule_entry.py` - ScheduleEntry model: FK to devices+users, weekday, start_time, end_time (no subject)
- `app/models/attendance_token.py` - AttendanceToken model: token UUID, device+schedule FKs, lesson_date, expiry
- `app/models/attendance_record.py` - AttendanceRecord model: student+token FKs, checked_in_at, UniqueConstraint
- `app/models/__init__.py` - Imports all 5 models to register them on Base metadata
- `app/main.py` - FastAPI app with asynccontextmanager lifespan calling Base.metadata.create_all()
- `requirements.txt` - 10 pinned packages for reproducible builds

## Decisions Made

- Used SQLAlchemy 2.0 `Mapped[]` + `mapped_column()` pattern throughout — consistent with Base(DeclarativeBase) from Plan 01
- Pinned all 10 packages in requirements.txt now (including paho-mqtt, python-jose, passlib, apscheduler) to prevent Docker layer cache invalidation when Phase 6 adds MQTT
- `import app.models  # noqa: F401` in main.py ensures create_all() sees all 5 tables at startup

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The plan's Task 2 verify command `python -c "from app.main import app"` fails without a `.env` file or env vars, because `app.database` imports `get_settings()` which requires `SECRET_KEY`. This is expected — `.env` is created in Plan 03. Verification was run as `SECRET_KEY=test-key DATABASE_URL=sqlite:////:memory: python -c "from app.main import app; print(app.title)"` which succeeds. Tests (which use conftest.py env injection) all pass normally.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 5 models ready for import by auth, admin, teacher, check-in, and MQTT phases
- FastAPI app boots and creates tables on startup
- requirements.txt ready for Plan 03 Docker Compose configuration
- test_all_tables_created is functionally green (xpassed) — the xfail marker can be removed in a future cleanup

---
*Phase: 01-foundation*
*Completed: 2026-03-27*
