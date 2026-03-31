# Phase 1: Foundation - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver the project scaffold that every subsequent phase builds on: directory layout, all 5 SQLAlchemy models with their exact fields, Docker Compose stack that boots server + MQTT broker + 3 dummy client stubs, pydantic-settings config, multi-arch Dockerfile, Mosquitto config, and `.env.example`.

No business logic, no authentication, no UI — just a clean, bootable foundation.

</domain>

<decisions>
## Implementation Decisions

### App Package Layout
- **D-01:** All application code lives under `app/` subdirectory. Structure:
  ```
  SmartAttend/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py
  │   ├── config.py
  │   ├── database.py
  │   ├── models/
  │   ├── routers/
  │   ├── services/
  │   ├── templates/
  │   └── static/
  ├── dummy_client/
  ├── mosquitto/
  ├── docker-compose.yml
  └── Dockerfile
  ```
- **D-02:** Imports use `app.models.user`, `app.routers.auth`, etc.

### Database Initialization
- **D-03:** Use `SQLAlchemy Base.metadata.create_all()` called in FastAPI lifespan on startup. No Alembic. Tables are created automatically on first boot inside Docker.

### User Model
- **D-04:** Fields: `id` (int PK), `email` (str, unique), `first_name` (str), `last_name` (str), `role` (str enum: admin/teacher/student), `class_name` (str, nullable — used for students, e.g. "10A"), `password_hash` (str), `is_active` (bool, default True)

### Device Model
- **D-05:** Fields: `id` (int PK), `device_id` (str, unique — MQTT client identifier), `room` (str, nullable), `label` (str, nullable), `is_enabled` (bool, default False — admin-controlled), `is_online` (bool, default False — heartbeat-controlled), `last_seen` (datetime, nullable), `last_lux` (float, nullable)

### ScheduleEntry Model
- **D-06:** Fields: `id` (int PK), `device_id` (int FK → Device), `teacher_id` (int FK → User), `class_name` (str — e.g. "10A"), `weekday` (int, 0=Monday–6=Sunday), `start_time` (time), `end_time` (time)
- **D-07:** No `subject` field — dropped by user decision.

### AttendanceToken Model
- **D-08:** Fields: `id` (int PK), `token` (str UUID, unique, indexed), `device_id` (int FK → Device), `schedule_entry_id` (int FK → ScheduleEntry), `lesson_date` (date — the specific calendar date of the lesson), `is_active` (bool, default True), `created_at` (datetime), `expires_at` (datetime)
- **D-09:** `lesson_date` enables per-day attendance records for recurring weekly schedule entries.

### AttendanceRecord Model
- **D-10:** Fields: `id` (int PK), `student_id` (int FK → User), `token_id` (int FK → AttendanceToken), `checked_in_at` (datetime)
- **D-11:** Unique constraint on `(student_id, token_id)` prevents duplicate check-ins (CHKIN-04).

### Claude's Discretion
- Dummy client stub form in Phase 1: whether `docker-compose.yml` references placeholder image vs minimal Python — Claude decides based on what makes `docker compose up` succeed cleanly.
- Exact `mosquitto.conf` content (anonymous access, listener port 1883) — standard config for prototype.
- `.env.example` variable names — derive from what config.py needs (SECRET_KEY, DATABASE_URL, MQTT_BROKER, MQTT_PORT, SERVER_IP, etc.).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — FOUND-01 through FOUND-08 define all Phase 1 acceptance criteria

### Project Context
- `.planning/PROJECT.md` — Tech stack constraints, key decisions (JWT cookie durations, Pico CSS from static/, SQLite)

No external specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — this is a greenfield project. Phase 1 creates the first code.

### Established Patterns
- None yet — Phase 1 establishes the patterns all subsequent phases will follow.

### Integration Points
- `app/main.py` FastAPI app instance — routers from later phases attach here
- `app/database.py` session factory — all routes in later phases depend on this
- `app/models/` — all 5 models defined here; later phases import and query them

</code_context>

<specifics>
## Specific Ideas

- User confirmed camelCase field names were their mental model but Python snake_case will be used in implementation (e.g. `first_name` not `firstName`, `password_hash` not `passwordHash`).
- `lesson_date` on AttendanceToken was explicitly requested — enables distinguishing Monday Jan 6 from Monday Jan 13 for the same recurring schedule entry.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2026-03-27*
