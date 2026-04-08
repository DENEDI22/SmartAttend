# Stack Research

**Domain:** QOL improvements to existing FastAPI attendance system
**Researched:** 2026-04-08
**Confidence:** HIGH

## Key Finding: No New Dependencies Required

Every v1.2 feature can be built with Python stdlib + existing pinned dependencies. Adding libraries would be unjustified complexity for a school prototype on a Raspberry Pi.

## Feature-by-Feature Stack Analysis

### CSV Import (Users + Schedule Entries)

| Need | Solution | Already Available |
|------|----------|-------------------|
| Parse CSV uploads | Python `csv` stdlib module | YES -- already used in teacher CSV export |
| Accept file uploads | `python-multipart` (pinned 0.0.22) + FastAPI `UploadFile` | YES -- in requirements.txt |
| Validate rows | Manual validation in Python | YES -- no library needed |
| Show preview with errors | Jinja2 template rendering | YES -- existing pattern |
| Template download | Static CSV file or `StreamingResponse` | YES -- existing CSV export pattern in `teacher.py` |

**Why no pandas/openpyxl:** CSV is the only format needed. The `csv` stdlib handles parsing, `UploadFile` handles the multipart form. Adding pandas (50MB+ with numpy) to a Pi image for trivial CSV parsing is wasteful.

**Validation approach:** Read uploaded bytes, decode UTF-8 (handle BOM like existing export does), parse with `csv.DictReader`, validate each row against known fields (email format, role enum, weekday range, time format). Return a list of `{row_num, data, errors}` dicts to the template for preview rendering.

**Encoding note:** The existing CSV export writes UTF-8 BOM (`\ufeff`). The import should handle both BOM and non-BOM UTF-8 input. `codecs.BOM_UTF8` or strip `\ufeff` from the first field.

### Student Dashboard

| Need | Solution | Already Available |
|------|----------|-------------------|
| Aggregate attendance stats | SQLAlchemy queries with `func.count()` | YES -- SQLAlchemy 2.0.48 |
| Join attendance records to schedule/tokens | SQLAlchemy relationships/joins | YES -- foreign keys exist |
| Render dashboard HTML | Jinja2 templates + Pico CSS | YES -- existing pattern |

**Query pattern:** Join `AttendanceRecord` -> `AttendanceToken` -> `ScheduleEntry`, filter by `student_id` and `class_name`. Group by `schedule_entry_id` + `lesson_date` for per-lesson detail. Use `func.count()` for summary stats (total lessons, attended, late, missed).

**No ORM changes needed for dashboard itself** -- all data is queryable from existing tables via joins.

### Password Change (Self-Service + Admin Reset)

| Need | Solution | Already Available |
|------|----------|-------------------|
| Hash new password | `passlib` + `bcrypt` (pinned) | YES -- `get_password_hash()` in `auth.py` |
| Verify old password | `verify_password()` | YES -- in `auth.py` |
| Form handling | FastAPI `Form(...)` | YES -- existing pattern in `auth.py`, `admin.py` |

**Self-service flow:** POST with `current_password` + `new_password` + `confirm_password`. Verify current password with existing `verify_password()`, hash new one with `get_password_hash()`, update `user.password_hash`.

**Admin reset flow:** POST with `new_password` for target user. No current password check needed (admin privilege). Same `get_password_hash()`.

### Late Threshold ("Verspaetet")

| Need | Solution | Already Available |
|------|----------|-------------------|
| Store global default | New field on `Settings` / config | Pydantic Settings -- YES |
| Store per-entry override | New nullable column on `ScheduleEntry` | SQLAlchemy migration -- YES |
| Compute late status | Compare `checked_in_at` vs `start_time + threshold` | Python `datetime` arithmetic -- YES |

**Model change:** Add `late_threshold_minutes: Mapped[int | None]` to `ScheduleEntry` (nullable = use global default). Add `LATE_THRESHOLD_MINUTES: int = 15` to `Settings` class (env-configurable via `LATE_THRESHOLD_MINUTES`).

**Late computation:** `checked_in_at > datetime.combine(lesson_date, start_time) + timedelta(minutes=threshold)` means late. This is a pure Python computation, no library needed.

### Remove Lux Reading Feature

| Need | Solution | Already Available |
|------|----------|-------------------|
| Remove MQTT handler | Delete `_handle_lux()` from `mqtt.py` | Code deletion only |
| Remove subscription | Remove `sensors/+/lux` from subscription list | Code deletion only |
| Remove model field | Drop `last_lux` from `Device` model | SQLAlchemy column removal |
| Remove UI references | Remove from any admin templates | Template edit only |

**Pure deletion task.** No new dependencies.

### Extend Token Validity (60s -> 90s)

**Current state:** Token `expires_at` is set to `datetime.combine(today, entry.end_time)` in `scheduler.py:71` -- tokens already expire at lesson end, not after 60s. The 60s likely refers to the token issuance interval (how often new tokens are generated). Need to verify the scheduler interval config.

**Change:** Adjust the APScheduler interval or the token expiry logic. Both use existing `apscheduler` (3.11.2) and `datetime` -- no new deps.

### Remove JWT 1h Expiry for Students

**Current state:** `auth.py` line 63: `expires = timedelta(hours=1)` for students, `timedelta(hours=8)` for teachers/admins.

**Change:** Set student JWT to `timedelta(days=365)` or similar very long duration (effectively "until logout"). The `python-jose` JWT library handles any `timedelta` -- no change needed.

**Cookie change:** Update `max_age` on the HTTP-only cookie to match. Already computed from `expires.total_seconds()`.

## Recommended Stack (Unchanged)

### Core Technologies -- NO CHANGES

| Technology | Version | Purpose | Status for v1.2 |
|------------|---------|---------|-----------------|
| FastAPI | 0.135.2 | Web framework | Sufficient -- UploadFile, Form, Response all available |
| SQLAlchemy | 2.0.48 | ORM + queries | Sufficient -- aggregation queries, schema changes |
| Jinja2 | 3.1.6 | Templates | Sufficient -- dashboard, CSV preview, password forms |
| Pico CSS | local | Styling | Sufficient -- tables, forms, badges for late status |
| python-jose | 3.5.0 | JWT auth | Sufficient -- expiry change is config only |
| passlib + bcrypt | 1.7.4 / 3.2.2 | Password hashing | Sufficient -- already has hash/verify functions |
| APScheduler | 3.11.2 | Token scheduling | Sufficient -- interval config change only |
| paho-mqtt | 2.1.0 | MQTT client | Sufficient -- removing lux subscription |
| python-multipart | 0.0.22 | File uploads | Sufficient -- needed for UploadFile (already installed) |
| pydantic-settings | 2.13.1 | Configuration | Sufficient -- add late threshold setting |

### Supporting Libraries -- NO ADDITIONS

| Stdlib Module | Purpose | Used By |
|---------------|---------|---------|
| `csv` | CSV parsing and writing | CSV import + existing CSV export |
| `io.StringIO` | In-memory CSV streams | CSV import validation + existing export |
| `datetime` | Late threshold computation | Late status calculation |
| `codecs` | BOM handling for CSV | CSV import encoding detection |

### Development Tools -- NO CHANGES

| Tool | Purpose | Notes |
|------|---------|-------|
| pytest | Testing | Existing -- 75 tests passing |
| httpx | Test client | Existing -- FastAPI TestClient |
| Docker Compose | Deployment | Existing -- 3-container stack |

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| pandas | 50MB+ dependency for trivial CSV parsing on a Pi | `csv` stdlib (already used in project) |
| openpyxl / xlsxwriter | Scope creep -- CSV is the agreed format | `csv` stdlib |
| WTForms / flask-wtf | FastAPI has native form handling with `Form(...)` | FastAPI `Form()` + manual validation |
| Alembic | Overkill for prototype with 7 tables, SQLite | `metadata.create_all()` + manual column adds |
| celery / dramatiq | No async tasks needed -- CSV validation is synchronous | Inline validation in request handler |
| chardet / charset-normalizer | CSV files will be UTF-8 (matching export format) | Manual BOM detection with `codecs` |

## Database Schema Changes Required

These are model-level changes, not new dependencies:

| Model | Change | Purpose |
|-------|--------|---------|
| `ScheduleEntry` | Add `late_threshold_minutes: int \| None` (nullable) | Per-entry late threshold override |
| `Device` | Remove `last_lux: float \| None` | Lux feature removal |
| `Settings` (config) | Add `late_threshold_minutes: int = 15` | Global late threshold default |

**Migration strategy:** Since this is a prototype using SQLite with `metadata.create_all()`, new nullable columns can be added by recreating tables or using raw `ALTER TABLE ADD COLUMN`. Removing `last_lux` can wait (nullable column, no harm keeping it) or be done via table recreation. No Alembic needed.

## Integration Points

| Feature | Touches |
|---------|---------|
| CSV import | New router endpoints, new templates, existing `get_password_hash()` for user import |
| Student dashboard | New router (or extend existing), new templates, existing models via joins |
| Password change | New endpoints on auth router, existing `verify_password()` + `get_password_hash()` |
| Late threshold | `ScheduleEntry` model, `Settings` config, teacher + student dashboard templates |
| Lux removal | `mqtt.py` handler, `Device` model, admin templates |
| Token validity | `scheduler.py` timing config |
| JWT expiry | `auth.py` line 63, cookie `max_age` |

## Version Compatibility

No compatibility concerns -- all changes use existing pinned versions. The stack is frozen at known-working versions from v1.1.

| Package | Version | Concern | Status |
|---------|---------|---------|--------|
| python-multipart | 0.0.22 | Needed for `UploadFile` | Already installed, never used yet -- will activate for CSV import |
| FastAPI | 0.135.2 | `UploadFile` API stable since 0.68+ | No concern |
| SQLAlchemy | 2.0.48 | `func.count()`, joins, nullable columns | No concern |

## Sources

- Existing codebase analysis: `requirements.txt`, `app/services/auth.py`, `app/routers/teacher.py` (CSV export pattern), `app/services/scheduler.py`, `app/services/mqtt.py`, `app/config.py`, all models
- Python stdlib `csv` module -- standard library, no version concern
- FastAPI `UploadFile` -- documented feature, `python-multipart` already a dependency

---
*Stack research for: SmartAttend v1.2 QOL Improvements*
*Researched: 2026-04-08*
