# Architecture Patterns

**Domain:** QOL improvements integration into existing NFC attendance tracking system
**Researched:** 2026-04-08

## Existing Architecture Summary

```
FastAPI app (main.py)
  |-- routers/auth.py      (login, logout, /auth/me, /student landing)
  |-- routers/admin.py     (devices, users, schedule CRUD)
  |-- routers/teacher.py   (dashboard, lesson detail, CSV export)
  |-- routers/checkin.py   (NFC token -> attendance record)
  |-- services/auth.py     (password hashing, JWT creation, user lookup)
  |-- services/mqtt.py     (device register, heartbeat, lux handler, token publish)
  |-- services/scheduler.py (token issuance every 1min, heartbeat check every 30s)
  |-- dependencies.py      (get_current_user, require_role)
  |-- config.py            (Settings via pydantic-settings)
  |-- models/              (User, Device, ScheduleEntry, AttendanceToken, AttendanceRecord, SchoolClass)
  |-- templates/           (Jinja2 + Pico CSS, base/admin_base/teacher_base/student_base)
```

## Feature-by-Feature Integration Analysis

### 1. Student Dashboard

**What exists:** `routers/auth.py` has a placeholder `GET /student` that renders `student.html` (just says "tap your phone"). `student_base.html` has logout button only.

**New components:**
- **New router:** `routers/student.py` -- extract student routes from `auth.py`, add dashboard logic
- **Modified template:** `student.html` -- replace placeholder with attendance summary + lesson list
- **Modified template:** `student_base.html` -- add nav link to dashboard

**Data flow:**
```
GET /student (require_role("student"))
  -> Query ScheduleEntry WHERE class_name = user.class_name
  -> For each entry, query AttendanceToken + AttendanceRecord for this student
  -> Compute: total lessons, attended, missed, late (needs late threshold)
  -> Render student_dashboard.html with summary stats + lesson table
```

**Integration points:**
- Queries join ScheduleEntry -> AttendanceToken -> AttendanceRecord, same pattern as `teacher.py:_build_roster`
- Student sees only their own records filtered by `class_name` match
- "Late" status depends on late threshold feature (see item 3) -- build dashboard first with present/absent, add late column after threshold is implemented
- Move `GET /student` route from `auth.py` to new `student.py` router

**Key consideration:** The dashboard must show historical data (not just today), so it needs to query across all lesson dates. Group by ScheduleEntry + lesson_date to enumerate past lessons.

### 2. Password Change

**What exists:** `services/auth.py` has `get_password_hash()` and `verify_password()`. No password change endpoint.

**New components:**
- **New route in auth.py:** `GET /auth/change-password` + `POST /auth/change-password` -- self-service for any logged-in user
- **New route in admin.py:** `POST /admin/users/{user_id}/reset-password` -- admin resets any user's password
- **New template:** `change_password.html`
- **Modified template:** `admin_users.html` -- add reset-password form/button per user row

**Data flow (self-service):**
```
POST /auth/change-password (require get_current_user)
  -> Form: current_password, new_password, confirm_password
  -> verify_password(current, user.password_hash)
  -> Validate new_password == confirm_password
  -> user.password_hash = get_password_hash(new_password)
  -> db.commit()
  -> Redirect with success message
```

**Data flow (admin reset):**
```
POST /admin/users/{user_id}/reset-password (require_role("admin"))
  -> Form: new_password
  -> user.password_hash = get_password_hash(new_password)
  -> db.commit()
  -> Redirect to /admin/users with success message
```

**Integration points:**
- Uses existing `verify_password` and `get_password_hash` from `services/auth.py` -- no new service code needed
- Self-service route uses `get_current_user` dependency (not role-specific, all roles can change password)
- Admin reset uses `require_role("admin")` -- existing pattern
- Add "Passwort aendern" link to all base templates (admin_base, teacher_base, student_base) in the nav

**No model changes required.**

### 3. Late Threshold ("Verspaetet")

**What exists:** `AttendanceRecord.checked_in_at` stores the check-in timestamp. `ScheduleEntry.start_time` stores lesson start. No late threshold anywhere.

**New components:**
- **Modified model:** `ScheduleEntry` -- add `late_threshold_minutes: Mapped[int | None]` (nullable, None = use global default)
- **Modified config:** `Settings` -- add `default_late_threshold_minutes: int = 15`
- **Modified model (optional):** `AttendanceRecord` -- no change needed, late status is computed at query time
- **Modified template:** `admin_devices.html` -- add late threshold field to schedule entry form
- **Modified templates:** `teacher_lesson.html`, `teacher_dashboard.html` -- show "Verspaetet" status
- **Modified template:** student dashboard -- show late status

**Data flow (late computation):**
```python
def is_late(record: AttendanceRecord, entry: ScheduleEntry, settings: Settings) -> bool:
    threshold = entry.late_threshold_minutes or settings.default_late_threshold_minutes
    lesson_start = datetime.combine(record.checked_in_at.date(), entry.start_time)
    cutoff = lesson_start + timedelta(minutes=threshold)
    return record.checked_in_at > cutoff
```

**Integration points:**
- Late is a **computed property**, not stored -- this avoids migration complexity and means changing the threshold retroactively recomputes history
- `_build_roster()` in `teacher.py` currently returns status as "Anwesend"/"Abwesend" -- extend to "Verspaetet" by comparing `checked_in_at` against `start_time + threshold`
- Add `late_threshold_minutes` column to ScheduleEntry, with nullable + default None (means "use global")
- Global default goes in `config.py` Settings, read from `.env` as `DEFAULT_LATE_THRESHOLD_MINUTES=15`
- Admin schedule form gets an optional "Verspaetungs-Schwelle (Min)" field
- Teacher CSV export gets a "Verspaetet" column

**DB migration:** SQLite + `create_all()` means adding a nullable column is straightforward (new column gets NULL for existing rows, which means "use global default").

### 4. CSV Import (Users + Schedule Entries)

**What exists:** Admin can create users one-at-a-time via form. No bulk import.

**New components:**
- **New routes in admin.py:**
  - `GET /admin/users/csv-template` -- download empty CSV template for users
  - `POST /admin/users/csv-upload` -- upload CSV, parse, return validation preview
  - `POST /admin/users/csv-confirm` -- confirm import after preview
  - `GET /admin/schedule/csv-template` -- download empty CSV template for schedule
  - `POST /admin/schedule/csv-upload` -- upload CSV, parse, return validation preview
  - `POST /admin/schedule/csv-confirm` -- confirm import after preview
- **New templates:**
  - `admin_csv_preview.html` -- show parsed rows with error highlighting, confirm button
- **New service (optional):** `services/csv_import.py` -- parsing + validation logic

**Data flow (two-step: upload -> preview -> confirm):**
```
Step 1: POST /admin/users/csv-upload
  -> Accept UploadFile
  -> Parse CSV (semicolon delimiter, UTF-8 BOM handling -- match export format)
  -> Validate each row:
    - Required fields present (email, first_name, last_name, role)
    - Email format valid
    - Email not duplicate (in file + vs DB)
    - Role in (admin, teacher, student)
    - class_name present if student
  -> Return preview template with rows + error annotations
  -> Store parsed data in hidden form fields or session

Step 2: POST /admin/users/csv-confirm
  -> Re-validate (defense in depth)
  -> Bulk create User objects with generated passwords or provided passwords
  -> Auto-create SchoolClass entries as needed
  -> Redirect with success count
```

**Integration points:**
- Uses existing `get_password_hash` for bulk password hashing
- Uses existing `check_schedule_conflict` for schedule import validation
- Reuses existing `SchoolClass` auto-creation pattern from `users_create`
- CSV format should match the existing CSV export format (semicolon delimiter, UTF-8 BOM) for consistency
- For schedule CSV: validate device_id exists, teacher email exists, no time conflicts
- Preview state: pass validated rows as hidden form fields (no server-side session state -- keeps the app stateless)

**Key design decision:** Use hidden form fields for preview-to-confirm state, not server sessions. This keeps the app stateless (no session backend needed for SQLite/RPi deployment).

### 5. Lux Removal

**What exists:**
- `Device.last_lux` column in model
- `mqtt.py`: `_handle_lux()` handler, `sensors/+/lux` subscription in `_on_connect`
- `admin_devices.html`: Lux column in device table
- `dummy_client/main.py`: `lux_loop()` function, `LUX_VALUE` env var
- Tests: `test_mqtt.py::test_lux_update`, `test_dummy_client.py::test_lux_publishes`

**Components to modify:**
- **Modified model:** `Device` -- remove `last_lux` column (or leave nullable and just stop using it)
- **Modified service:** `mqtt.py` -- remove `_handle_lux()`, remove `sensors/+/lux` from subscription list
- **Modified template:** `admin_devices.html` -- remove Lux `<th>` and `<td>`
- **Modified client:** `dummy_client/main.py` -- remove `lux_loop()`, `LUX_VALUE`
- **Modified tests:** Remove `test_lux_update`, `test_lux_publishes`

**Integration points:**
- Pure deletion -- no new functionality, no dependencies from other features
- DB column removal: with SQLite + `create_all()`, the column will remain in existing DBs but stop being written. For a clean install, it won't appear. This is acceptable for a prototype -- no Alembic migration needed.
- ESP32 firmware (`SmartAttend.ino`) has NO lux code, so no firmware changes needed.

**Recommendation:** Remove the `last_lux` field from the Device model entirely. Existing databases will have the column but it's harmless (SQLAlchemy won't query it if the model doesn't map it). For production, drop column via manual SQL if needed.

### 6. 90s Token Validity

**What exists:** In `scheduler.py:_issue_tokens()`, tokens are issued every 1 minute with `expires_at = datetime.combine(today, entry.end_time)`. The token validity is actually the entire lesson duration (not 60s). The "60s" refers to the **scheduler rotation interval** -- a new token is issued every 60 seconds, replacing the previous one.

**Clarification needed:** The requirement says "extend check-in token validity from 60s to 90s." Looking at the code:
- `_issue_tokens` runs every 1 minute (IntervalTrigger(minutes=1))
- Each token's `expires_at` is set to lesson end time (not +60s)
- Previous tokens are deactivated (`is_active=False`) when a new one is issued
- Students can check in with ANY token for the same schedule_entry + lesson_date (the cross-token lookup pattern)

**What "60s to 90s" likely means:** Change the scheduler interval from 1 minute to 1.5 minutes (90 seconds), so tokens rotate less frequently and the NFC tag holds a valid URL longer.

**Components to modify:**
- **Modified service:** `scheduler.py` -- change `IntervalTrigger(minutes=1)` to `IntervalTrigger(seconds=90)`
- **Modified config (optional):** Add `token_rotation_seconds: int = 90` to Settings for configurability

**Integration points:**
- Single line change in `scheduler.py`
- No model changes, no template changes
- The cross-token attendance lookup pattern means even if a student scans an old token, they can still check in -- this is already handled
- Consider making configurable via `.env` for future tuning

### 7. JWT Expiry Changes (Students Stay Logged In)

**What exists:** In `routers/auth.py:login_post()`:
```python
if user.role == "student":
    expires = timedelta(hours=1)
else:
    expires = timedelta(hours=8)
```
Cookie `max_age` is set to `int(expires.total_seconds())`.

**Components to modify:**
- **Modified router:** `auth.py` -- change student JWT expiry to a very long duration (e.g., 365 days) or remove expiry entirely
- **Modified cookie:** Set `max_age` to match (or omit for session cookie)

**Design decision:** Use a very long expiry (e.g., 30 days) rather than no expiry. Reasons:
1. Truly infinite tokens are a security smell even for a prototype
2. 30 days is effectively "stay logged in" for a school term
3. The explicit logout still works (deletes cookie)

**Implementation:**
```python
if user.role == "student":
    expires = timedelta(days=30)  # Stay logged in until logout
else:
    expires = timedelta(hours=8)  # Teachers/admins: workday session
```

**Integration points:**
- Two lines changed in `auth.py`
- `dependencies.py:get_current_user()` already handles JWT expiry via `jose.jwt.decode()` which raises `ExpiredSignatureError` -- this continues to work correctly with the longer expiry
- Cookie `max_age` must match the JWT expiry so browser keeps the cookie
- No model changes, no template changes

**Security note:** The `get_current_user` dependency checks `user.is_active`, so deactivated students are still blocked even with a long-lived token. Admin can effectively "log out" a student by deactivating their account.

## Recommended Architecture

### New Router: `routers/student.py`

| Route | Method | Purpose |
|-------|--------|---------|
| `GET /student` | GET | Student dashboard with attendance summary |

Extracted from `auth.py` (currently a placeholder there). The `auth.py` retains login/logout/me routes.

### Modified Router: `routers/auth.py`

| Route | Method | Purpose |
|-------|--------|---------|
| `GET /auth/change-password` | GET | Password change form |
| `POST /auth/change-password` | POST | Process password change |

Remove `GET /student` (moved to student router).

### Modified Router: `routers/admin.py`

| Route | Method | Purpose |
|-------|--------|---------|
| `POST /admin/users/{user_id}/reset-password` | POST | Admin password reset |
| `GET /admin/users/csv-template` | GET | Download user CSV template |
| `POST /admin/users/csv-upload` | POST | Upload + validate user CSV |
| `POST /admin/users/csv-confirm` | POST | Confirm user CSV import |
| `GET /admin/schedule/csv-template` | GET | Download schedule CSV template |
| `POST /admin/schedule/csv-upload` | POST | Upload + validate schedule CSV |
| `POST /admin/schedule/csv-confirm` | POST | Confirm schedule CSV import |

### Model Changes

| Model | Change | Migration |
|-------|--------|-----------|
| `ScheduleEntry` | Add `late_threshold_minutes: Mapped[int \| None]` (nullable) | Auto via `create_all()` on new DB; existing DBs: column added as NULL by SQLite ALTER TABLE |
| `Device` | Remove `last_lux` field | Existing DBs: column stays but is unmapped (harmless) |

### Config Changes

| Setting | Default | Purpose |
|---------|---------|---------|
| `default_late_threshold_minutes` | `15` | Global late threshold |
| `token_rotation_seconds` | `90` | Scheduler token rotation interval |

### Template Changes

| Template | Change |
|----------|--------|
| `student.html` | Replace placeholder with dashboard (summary stats + lesson table) |
| `student_base.html` | Add nav links (dashboard, password change) |
| `admin_base.html` | Add "Passwort aendern" nav link |
| `teacher_base.html` | Add "Passwort aendern" nav link |
| `admin_devices.html` | Remove Lux column; add late_threshold field to schedule form |
| `admin_users.html` | Add password reset button per row; add CSV import section |
| `teacher_lesson.html` | Add "Verspaetet" status alongside "Anwesend" |
| `teacher_dashboard.html` | Show late count in lesson summary |
| `change_password.html` | **New** -- password change form |
| `admin_csv_preview.html` | **New** -- CSV import validation preview |

## Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `routers/student.py` | Student dashboard, attendance history view | models, dependencies |
| `routers/auth.py` | Login, logout, password change | services/auth, dependencies |
| `routers/admin.py` | User/device/schedule management, CSV import, password reset | models, services/auth |
| `routers/teacher.py` | Teacher dashboard with late status | models, config (for threshold) |
| `services/auth.py` | Password hashing, JWT creation | config |
| `services/mqtt.py` | Device communication (minus lux) | models |
| `services/scheduler.py` | Token rotation at configured interval | models, mqtt, config |
| `config.py` | App settings including new thresholds | .env |

## Data Flow Changes

### Late Status Computation (new)
```
ScheduleEntry.start_time + threshold_minutes -> cutoff_time
AttendanceRecord.checked_in_at > cutoff_time -> "Verspaetet"
```
Computed at query time in both teacher and student views. Not stored.

### CSV Import Flow (new)
```
Upload CSV -> Parse + Validate -> Render Preview with errors
  -> User confirms -> Re-validate -> Bulk insert -> Redirect with count
```
State passed via hidden form fields (stateless).

## Anti-Patterns to Avoid

### Anti-Pattern 1: Storing late status in the database
**What:** Adding an `is_late` boolean to AttendanceRecord
**Why bad:** If threshold changes, all historical records are wrong. Requires backfill migration.
**Instead:** Compute late status at query time from `checked_in_at` vs `start_time + threshold`.

### Anti-Pattern 2: Server-side session for CSV preview
**What:** Storing parsed CSV data in a server session between upload and confirm
**Why bad:** Requires session backend (Redis/files), breaks stateless design, complicates RPi deployment.
**Instead:** Pass validated data as hidden form fields in the preview page. Re-validate on confirm.

### Anti-Pattern 3: Removing the last_lux DB column via migration
**What:** Using Alembic or manual SQL to DROP COLUMN from existing databases
**Why bad:** SQLite has limited ALTER TABLE support (no DROP COLUMN before 3.35.0). Adds migration tooling complexity for a prototype.
**Instead:** Remove from model only. Existing DBs keep the column unmapped. New DBs don't get it.

### Anti-Pattern 4: Infinite JWT expiry for students
**What:** Setting no expiry on student JWTs
**Why bad:** Tokens live forever even if student leaves school. No natural expiry safety net.
**Instead:** Use 30-day expiry. Effectively "stay logged in" for a school term, but tokens eventually expire.

## Patterns to Follow

### Pattern 1: Computed Status at Query Time
**What:** Calculate "late" from timestamps + threshold, don't store it
**When:** Any derived boolean that depends on a configurable threshold
**Example:**
```python
threshold = entry.late_threshold_minutes or settings.default_late_threshold_minutes
cutoff = datetime.combine(lesson_date, entry.start_time) + timedelta(minutes=threshold)
status = "Verspaetet" if record.checked_in_at > cutoff else "Anwesend"
```

### Pattern 2: Two-Step Import (Upload -> Preview -> Confirm)
**What:** Parse and validate first, show user what will happen, then execute
**When:** Any bulk data operation where mistakes are costly
**Example:** CSV upload returns preview template with error annotations. Confirm button submits validated data via hidden fields.

### Pattern 3: Nullable Column = Use Global Default
**What:** `ScheduleEntry.late_threshold_minutes` is nullable; NULL means "use global from config"
**When:** Per-entity override of a global setting
**Example:**
```python
threshold = entry.late_threshold_minutes if entry.late_threshold_minutes is not None else settings.default_late_threshold_minutes
```

## Suggested Build Order

Build order is driven by dependencies between features:

```
Phase 1: Lux removal + 90s token + JWT expiry changes
  (Independent deletions/config changes, no dependencies, cleans up codebase)

Phase 2: Password change (self-service + admin reset)
  (Independent feature, no model changes, needed before student dashboard nav)

Phase 3: Late threshold (model change + computation logic)
  (Must exist before student dashboard can show late status)

Phase 4: Student dashboard
  (Depends on late threshold for full functionality)

Phase 5: CSV import
  (Most complex feature, independent of others, benefits from stable user/schedule models)
```

**Rationale:**
- Phases 1-2 are quick wins that clean up tech debt and add basic QOL
- Phase 3 before Phase 4 because the student dashboard should show late status from day one
- Phase 5 last because it's the most complex and doesn't block any other feature
- Each phase is independently deployable and testable

## Scalability Considerations

| Concern | Current (prototype) | If 500+ students |
|---------|--------------------|--------------------|
| Student dashboard queries | N+1 queries per lesson | Add eager loading, paginate lesson history |
| CSV import | Parse entire file in memory | Fine for school-scale (hundreds of rows) |
| Late computation | Computed per-request | Cache or materialize if needed |
| Token rotation | Single-threaded scheduler | Fine for single-school RPi |

Not a concern for prototype scale. SQLite handles school-scale reads well.

## Sources

- Direct codebase analysis (all files read and cross-referenced)
- Existing patterns in `teacher.py:_build_roster()` for attendance queries
- Existing patterns in `admin.py:users_create()` for user creation + SchoolClass auto-creation
- SQLite ALTER TABLE behavior: nullable columns can be added without migration tooling
