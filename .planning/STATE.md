---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: Milestone complete
stopped_at: Completed 07-dummy-clients-07-02-PLAN.md
last_updated: "2026-03-31T08:08:07.508Z"
progress:
  total_phases: 7
  completed_phases: 7
  total_plans: 18
  completed_plans: 18
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-27)

**Core value:** Students can check in to a lesson by tapping their phone on the classroom NFC device — the entire flow from tap to attendance record must work reliably.
**Current focus:** Phase 07 — dummy-clients

## Current Position

Phase: 07
Plan: Not started

## Performance Metrics

**Velocity:**

- Total plans completed: 0
- Average duration: -
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**

- Last 5 plans: none yet
- Trend: -

*Updated after each plan completion*
| Phase 01-foundation P01 | 3 | 2 tasks | 14 files |
| Phase 01-foundation P02 | 2 | 2 tasks | 8 files |
| Phase 01-foundation P03 | 3 | 2 tasks | 6 files |
| Phase 02-authentication P01 | 136s | 2 tasks | 3 files |
| Phase 02-authentication P02 | 138 | 2 tasks | 4 files |
| Phase 02-authentication P03 | 5min | 2 tasks | 7 files |
| Phase 03-admin-interface P01 | 564s | 2 tasks | 11 files |
| Phase 03-admin-interface P03 | 187 | 2 tasks | 4 files |
| Phase 03-admin-interface P02 | 739s | 2 tasks | 12 files |
| Phase 03-admin-interface P04 | 828 | 2 tasks | 5 files |
| Phase 04-teacher-interface P01 | 176s | 2 tasks | 6 files |
| Phase 04-teacher-interface P02 | 169s | 2 tasks | 3 files |
| Phase 05-student-check-in P01 | 190 | 2 tasks | 5 files |
| Phase 05-student-check-in P02 | 163s | 2 tasks | 3 files |
| Phase 06-mqtt-scheduler P01 | 161s | 1 tasks | 2 files |
| Phase 06-mqtt-scheduler P02 | 176 | 2 tasks | 4 files |
| Phase 07-dummy-clients P01 | 5min | 2 tasks | 2 files |
| Phase 07-dummy-clients P02 | 84s | 2 tasks | 0 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Init: Python dummy clients instead of real ESP32 (no hardware available during dev)
- Init: Docker Compose from Phase 1 (always deployable to RPi)
- Init: JWT in HTTP-only cookie (8h admin/teacher, 1h student)
- Init: Pico CSS from static/ (offline operation, no build step)
- Init: SQLite over PostgreSQL (zero config, sufficient for school prototype)
- [Phase 01-foundation]: SQLAlchemy 2.0 DeclarativeBase pattern used — required for Mapped[] typed columns in Plan 02
- [Phase 01-foundation]: pydantic-settings SettingsConfigDict pattern used — v2 API compliance, inner class Config silently broken
- [Phase 01-foundation]: lru_cache on get_settings() with cache_clear() in test fixtures — prevents settings bleed between tests
- [Phase 01-foundation]: ScheduleEntry has NO subject field — dropped per user decision D-07
- [Phase 01-foundation]: AttendanceRecord UniqueConstraint on (student_id, token_id) prevents duplicate check-ins (D-11)
- [Phase 01-foundation]: requirements.txt pins all 10 packages including later-phase deps to prevent Docker layer cache invalidation
- [Phase 01-foundation]: mosquitto.conf requires explicit listener 1883 + allow_anonymous true for Mosquitto 2.0 Docker networking
- [Phase 01-foundation]: DATABASE_URL uses sqlite:////app/data/smartattend.db (4 slashes) for absolute path inside container with bind mount
- [Phase 01-foundation]: dummy_client Phase 1 stub uses time.sleep(60) loop — Phase 7 replaces with full MQTT implementation
- [Phase 02-authentication]: Patch module-level engine in db_session fixture to prevent lifespan create_all hitting production DB path
- [Phase 02-authentication]: test_client uses follow_redirects=False to allow auth tests to inspect 303 redirects directly
- [Phase 02-authentication]: get_current_user raises HTTPException(303) not 401 — browser-friendly redirect for Jinja2 UI
- [Phase 02-authentication]: require_role raises 403 (not redirect) — authenticated but unauthorized user, different UX
- [Phase 02-authentication]: create_access_token takes explicit expires_delta — caller chooses 8h admin/teacher vs 1h student
- [Phase 02-authentication]: Template dir at app/templates — Jinja2Templates instantiated in router
- [Phase 02-authentication]: Admin seed placed in lifespan — idempotent, no-op if admin row exists
- [Phase 02-authentication]: bcrypt pinned to 4.x — bcrypt 5.x breaks passlib 1.7.4
- [Phase 03-admin-interface]: db_session.refresh() required after commit in test fixtures for SQLite in-memory session visibility
- [Phase 03-admin-interface]: Admin templates use two-level inheritance: admin_base.html extends base.html with nav and flash messages
- [Phase 03-admin-interface]: admin.js save-btn reads data-action from edit-form div for dynamic form URL
- [Phase 03-admin-interface]: SchoolClass auto-created on user create/update when class_name not in DB (D-14)
- [Phase 03-admin-interface]: div#edit-form with JS dynamic form submission avoids nested HTML forms for device table inline editing
- [Phase 03-admin-interface]: db_session.refresh() required after commit in admin_client fixture for SQLAlchemy session sync
- [Phase 03-admin-interface]: StaticPool required for in-memory SQLite test engine to prevent connection loss after commit in async handlers
- [Phase 03-admin-interface]: Half-open interval overlap detection [start, end) for schedule entries -- adjacent entries allowed
- [Phase 04-teacher-interface]: No Fach column in teacher dashboard -- ScheduleEntry has no subject field (D-07)
- [Phase 04-teacher-interface]: Room displayed from Device.room via device_id FK join (ScheduleEntry has no room field)
- [Phase 04-teacher-interface]: Teacher template pattern: teacher_base.html extends base.html with nav + flash messages
- [Phase 04-teacher-interface]: Shared _build_roster helper extracts roster logic for HTML and CSV endpoints
- [Phase 04-teacher-interface]: CSV uses semicolons, UTF-8 BOM, German filename Anwesenheit_{Klasse}_{YYYY-MM-DD}.csv
- [Phase 05-student-check-in]: student_base.html follows teacher_base.html pattern without flash messages
- [Phase 05-student-check-in]: checkin.html uses 4-state conditional rendering (error, already-checked-in, success, form)
- [Phase 05-student-check-in]: Manual auth check on GET /checkin to preserve token param in login redirect
- [Phase 05-student-check-in]: IntegrityError catch as safety net for concurrent duplicate check-ins
- [Phase 06-mqtt-scheduler]: NonClosingSession wrapper pattern for MQTT handler tests — prevents db.close() from detaching objects during assertions
- [Phase 06-mqtt-scheduler]: Per-callback SessionLocal pattern: each MQTT handler creates own session for thread safety
- [Phase 06-mqtt-scheduler]: NonClosingSession pattern reused for scheduler test DB isolation
- [Phase 06-mqtt-scheduler]: mqtt.py connect wrapped in try/except for graceful broker unavailability
- [Phase 06-mqtt-scheduler]: Lifespan ordering: MQTT starts before scheduler, scheduler stops before MQTT
- [Phase 07-dummy-clients]: importlib.reload with sys.path for testing standalone dummy_client module
- [Phase 07-dummy-clients]: stop_event.wait(timeout) pattern for graceful shutdown and testable periodic loops
- [Phase 07-dummy-clients]: Dockerfile and requirements.txt already correct from Plan 07-01 -- no changes needed for Plan 07-02

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-03-31T08:02:38.001Z
Stopped at: Completed 07-dummy-clients-07-02-PLAN.md
Resume file: None
