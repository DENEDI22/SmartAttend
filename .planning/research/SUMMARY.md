# Project Research Summary

**Project:** SmartAttend v1.2 QOL Improvements
**Domain:** NFC-based school attendance tracking system (incremental feature release)
**Researched:** 2026-04-08
**Confidence:** HIGH

## Executive Summary

SmartAttend v1.2 is a quality-of-life release for an existing, working NFC attendance system. The system already handles the core flow (ESP32 writes check-in URL to NFC tag, student taps phone, attendance recorded). This milestone adds the features that make the system usable in a real school: bulk CSV import (so admins don't manually create 200+ students), a student dashboard (so students can see their attendance), late tracking ("Verspaetet" -- standard in German schools), password management, and cleanup of dead code.

The recommended approach is conservative: zero new dependencies. Every feature builds on the existing FastAPI + SQLAlchemy + Jinja2 + Pico CSS stack using stdlib modules (notably `csv` for imports). The codebase already contains the patterns needed -- CSV export in `teacher.py`, password hashing in `auth.py`, attendance queries via JOIN chains. The work is integration and UI, not infrastructure. Schema changes are minimal (one new nullable column on ScheduleEntry, one column removal from Device, two new config values).

The primary risks are around CSV import data quality (encoding mismatches, duplicate records, partial failures) and datetime handling for the late threshold computation (naive vs timezone-aware datetime mixing). Both are preventable with disciplined validation-before-commit patterns and consistent use of naive datetimes throughout. The JWT expiry change has a subtle cookie `max_age` pitfall that will silently fail if not addressed. None of these risks justify architectural changes -- they require careful implementation.

## Key Findings

### Recommended Stack

No dependency changes. The existing pinned stack (FastAPI 0.135.2, SQLAlchemy 2.0.48, Jinja2 3.1.6, python-jose 3.5.0, passlib 1.7.4, APScheduler 3.11.2, paho-mqtt 2.1.0, python-multipart 0.0.22, pydantic-settings 2.13.1) handles every v1.2 feature. The `csv` stdlib module (already used for export) handles import parsing. The `python-multipart` package (already in requirements.txt but not yet used) enables `UploadFile` for CSV uploads.

**Core technologies (unchanged):**
- **FastAPI + Jinja2**: Web framework and templating -- UploadFile, Form(), server-rendered HTML all available
- **SQLAlchemy 2.0**: ORM -- func.count(), JOINs, nullable column additions, no Alembic needed
- **Python csv stdlib**: CSV parsing for import -- matches existing export pattern, no pandas needed
- **Pico CSS (local)**: Styling -- tables, forms, badges for late status, zero JS

**Explicitly rejected:** pandas (50MB on Pi for trivial CSV), Alembic (7-table prototype), WTForms (FastAPI has native forms), celery (no async tasks needed).

### Expected Features

**Must have (table stakes -- the system feels like a demo without these):**
- Student dashboard with attendance summary and lesson history
- Password change (self-service for all roles)
- Admin password reset for any user
- Late threshold tracking ("Verspaetet" with global default + per-entry override)
- CSV import for users (bulk creation of 200+ students)
- CSV import for schedule entries (bulk creation of 40+ weekly lessons)

**Should have (differentiators included in this milestone):**
- Late status displayed on student dashboard
- Attendance percentage calculation
- Remove dead lux reading code
- Extend token rotation from 60s to 90s
- Remove JWT 1h student expiry (use 30-day sessions)

**Defer (v2+):**
- Historical attendance view for teachers (past dates)
- PDF attendance reports
- Moodle integration, OAuth/SSO, MQTT authentication
- Real-time dashboard auto-refresh (would require WebSocket/JS)

### Architecture Approach

The architecture extends the existing router/service/model pattern with one new router (student.py extracted from auth.py) and new routes on existing routers (auth.py for password change, admin.py for CSV import and password reset). Late status is a computed property (not stored), calculated at query time from checked_in_at vs start_time + threshold. CSV import uses a two-step upload-preview-confirm flow with hidden form fields (no server sessions needed). All state remains stateless and RPi-friendly.

**Major components affected:**
1. **routers/student.py (NEW)** -- Student dashboard with attendance history via JOIN query
2. **routers/admin.py (EXTENDED)** -- CSV import (6 new routes), admin password reset
3. **routers/auth.py (EXTENDED)** -- Password change, JWT expiry adjustment, student route extraction
4. **services/mqtt.py (REDUCED)** -- Remove lux handler and subscription
5. **services/scheduler.py (TWEAKED)** -- Token rotation interval 60s to 90s
6. **config.py (EXTENDED)** -- default_late_threshold_minutes, token_rotation_seconds

### Critical Pitfalls

1. **JWT cookie max_age mismatch** -- Changing JWT expiry without updating the cookie max_age means the browser deletes the cookie before the JWT expires. Students still get logged out. Prevention: change BOTH in lockstep, test with a real browser.

2. **CSV import data corruption** -- German Excel exports Windows-1252 with semicolons. Duplicate emails with trailing whitespace create duplicate users. Partial imports leave inconsistent state. Prevention: validate entire CSV before any DB writes, use atomic transaction, normalize all strings, try UTF-8-sig then Latin-1 fallback.

3. **Naive datetime mixing in late threshold** -- The codebase uses naive datetime.now() everywhere except JWT creation (which uses UTC). Mixing aware and naive datetimes in the late calculation causes TypeError crashes. Prevention: keep all late computation in naive datetimes, add boundary tests.

4. **Student dashboard N+1 queries** -- Querying per-lesson on a Pi with SQLite is too slow for semester-length history. Prevention: single JOIN query with Python-side grouping, default to recent weeks with optional date range.

5. **NULL vs explicit late threshold confusion** -- Using NULL to mean "use global default" vs storing the actual default value. Prevention: NULL = use global, non-NULL = explicit override; display this distinction in UI.

## Implications for Roadmap

Based on dependency analysis and feature groupings, five phases in this order:

### Phase 1: Cleanup and Config Changes
**Rationale:** Independent, zero-risk changes that clean up tech debt and improve UX immediately. No feature dependencies. Can be done in a single session.
**Delivers:** Cleaner codebase, better student session persistence, slightly more reliable NFC check-ins.
**Addresses:** Remove lux reading, extend token rotation 60s to 90s, remove JWT 1h student expiry.
**Avoids:** Pitfall 1 (cookie max_age mismatch -- change JWT exp AND cookie together), Pitfall 8 (lux template references -- grep all references), Pitfall 10 (only change scheduler interval, not expires_at).

### Phase 2: Password Management
**Rationale:** Independent feature, no model changes, quick win with high user value. Should exist before the student dashboard (so the nav can include "Change Password" from the start).
**Delivers:** Self-service password change for all roles, admin password reset.
**Addresses:** Password change (self-service), admin password reset.
**Avoids:** Pitfall 6 (require current password for self-service, skip for admin reset), Pitfall 2 (document session invalidation limitation or add password_version to JWT).

### Phase 3: Late Threshold
**Rationale:** Must exist before the student dashboard so the dashboard shows the three-state German attendance model (Anwesend/Verspaetet/Abwesend) from day one. Requires a schema change (nullable column on ScheduleEntry) and config addition.
**Delivers:** Late detection logic, updated teacher roster and dashboard with "Verspaetet" status, per-entry override capability.
**Addresses:** Late threshold with global default + per-entry override, late status on teacher views.
**Avoids:** Pitfall 4 (naive datetime consistency), Pitfall 7 (NULL = use default pattern).

### Phase 4: Student Dashboard
**Rationale:** Depends on late threshold (Phase 3) for full functionality. Highest user-facing value -- students currently see a blank placeholder. Requires extracting student routes into a new router.
**Delivers:** Student attendance history, summary statistics (total/attended/missed/late/percentage), lesson list with status badges.
**Addresses:** Student dashboard, attendance percentage, late status on student view.
**Avoids:** Pitfall 5 (N+1 queries -- use single JOIN), Pitfall 12 (class transfer -- follow record chain, not current class_name).

### Phase 5: CSV Import
**Rationale:** Most complex feature (HIGH implementation cost), independent of other features, benefits from stable models after Phases 1-4. Two sub-features: user import first (teachers must exist before schedule import can reference them).
**Delivers:** Bulk user creation from CSV, bulk schedule entry creation from CSV, template downloads, validation preview with error highlighting.
**Addresses:** CSV user import, CSV schedule import.
**Avoids:** Pitfall 3 (validate-then-commit, atomic transactions, duplicate detection), Pitfall 9 (UTF-8-sig with Latin-1 fallback, semicolon delimiter, BOM handling).

### Phase Ordering Rationale

- Phases 1-2 first because they are quick wins (config changes, simple forms) that deliver immediate value and clean up the codebase before building new features on top.
- Phase 3 before Phase 4 because the student dashboard should show three-state attendance from its first deployment. Building the dashboard without late status and retrofitting it later means touching the same templates twice.
- Phase 5 last because it is the most complex feature (6 new routes, CSV parsing, validation preview, encoding handling) and has zero dependencies on other features. It also benefits from stable User and ScheduleEntry models after schema changes in Phase 3.
- User CSV import before schedule CSV import within Phase 5 because schedule entries reference teachers by email -- teachers must be importable first.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 5 (CSV Import):** Complex validation logic, encoding edge cases, hidden-form-field state management for preview-to-confirm flow. Needs careful spec of validation rules and error UX.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Cleanup):** Pure deletion and config changes. Locations are known, changes are one-liners.
- **Phase 2 (Password Management):** Standard form handling, existing verify_password/get_password_hash functions. Well-documented FastAPI pattern.
- **Phase 3 (Late Threshold):** Straightforward datetime arithmetic, nullable column addition. Pattern is clear from research.
- **Phase 4 (Student Dashboard):** Follows existing teacher.py _build_roster() query pattern. Main concern (N+1) has a documented solution (single JOIN).

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All dependencies already pinned and tested in v1.1. Zero additions needed. Direct codebase verification. |
| Features | HIGH | Features derived from explicit project requirements. Scope is well-defined. Competitor analysis confirms German school conventions. |
| Architecture | HIGH | Integration points mapped against actual codebase files. Existing patterns (CSV export, password hashing, role-based routing) directly reusable. |
| Pitfalls | HIGH | Pitfalls identified from direct code reading (JWT cookie handling, datetime usage, SQLite limitations). One MEDIUM item: python-jose exp claim behavior should be verified in a test. |

**Overall confidence:** HIGH

### Gaps to Address

- **Password version for session invalidation:** Research identified that password change does not invalidate existing JWTs. Adding password_version to the JWT is the clean solution but adds a model column and changes the auth flow. Decision needed: implement it (more secure) or document the limitation (simpler). Recommend: implement it -- it is a small change with meaningful security benefit.
- **Student dashboard date scoping:** Research does not prescribe exact UX for how far back the dashboard shows. Options: current week, current month, all time with pagination. Decide during Phase 4 planning.
- **CSV import: reject-all vs skip-bad-rows:** Two valid approaches for handling rows with errors. Reject-all is safer (forces clean data). Skip-bad-rows is more practical for schools with messy data. Decide during Phase 5 planning.
- **SQLite version on target RPi:** Lux column removal assumes SQLAlchemy ignores unmapped columns (verified). But if a future phase needs DROP COLUMN, need to confirm SQLite >= 3.35.0 on the deployment target.

## Sources

### Primary (HIGH confidence)
- Direct codebase analysis: all models, routers, services, templates, tests, requirements.txt
- Python stdlib csv module documentation
- FastAPI UploadFile and Form() documentation
- SQLAlchemy 2.0 mapped column and query API

### Secondary (MEDIUM confidence)
- python-jose JWT exp claim handling (training data -- verify with test)
- SQLite ALTER TABLE ADD COLUMN behavior (well-documented but version-dependent)
- German school attendance conventions (Anwesend/Verspaetet/Abwesend three-state model)

---
*Research completed: 2026-04-08*
*Ready for roadmap: yes*
