# Phase 4: Teacher Interface - Context

**Gathered:** 2026-03-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Teachers can monitor live attendance for their lessons and export records. Dashboard shows today's lessons with check-in counts, detail view shows full class roster with attendance status, CSV export downloads the roster. All UI in German, using Pico CSS classless styling.

</domain>

<decisions>
## Implementation Decisions

### Dashboard Layout
- **D-01:** Table view for today's lessons at `/teacher`. Columns: Klasse, Raum, Zeit, Anwesend (X/Y), Details-Link. Table rows are read-only — no inline editing.
- **D-02:** "Expected student count" is calculated by counting active students with matching `class_name`: `SELECT COUNT(*) FROM users WHERE role='student' AND class_name = schedule_entry.class_name AND is_active = True`.
- **D-03:** "Checked-in count" is the number of AttendanceRecords linked to the AttendanceToken for that schedule_entry + today's date.
- **D-04:** Only show lessons for today (current weekday) where the teacher_id matches the logged-in teacher.

### Attendance List View
- **D-05:** Full class roster at `/teacher/lesson/<token_id>`. Shows ALL students in the class, not just those checked in. Columns: Name (Nachname, Vorname), Status (✓ Anwesend / — Abwesend), Uhrzeit (check-in time or empty).
- **D-06:** Header shows: class name, room, time range, and "Anwesend: X/Y" summary.
- **D-07:** "CSV herunterladen" link below the table to download attendance as CSV.

### CSV Export
- **D-08:** Full roster with status. Columns: Nachname;Vorname;Klasse;Status;Uhrzeit. Semicolon separator (German Excel default).
- **D-09:** UTF-8 encoding with BOM for Excel compatibility.
- **D-10:** Filename format: `Anwesenheit_{Klasse}_{YYYY-MM-DD}.csv`. E.g., `Anwesenheit_10A_2026-03-29.csv`.
- **D-11:** Absent students have empty Uhrzeit field.

### Nav & Page Structure
- **D-12:** Separate `teacher_base.html` extending `base.html`. Same pattern as `admin_base.html`. Nav: SmartAttend brand, Übersicht link, Abmelden button.
- **D-13:** Teacher router at `app/routers/teacher.py` with prefix `/teacher`. All routes protected by `require_role("teacher")`.
- **D-14:** Flash messages via query params (same `?msg=` / `?error=` pattern as admin).

### Claude's Discretion
- Empty state when teacher has no lessons today ("Heute keine Stunden geplant")
- Sorting order of attendance list (alphabetical by last name)
- How to handle the case where AttendanceToken doesn't exist yet (lesson hasn't started, scheduler hasn't issued token)
- Template file naming (teacher_dashboard.html, teacher_lesson.html, etc.)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements fully captured in decisions above and REQUIREMENTS.md (TEACH-01 through TEACH-04).

### Codebase References
- `app/models/schedule_entry.py` — ScheduleEntry model (device_id, teacher_id, class_name, weekday, start_time, end_time)
- `app/models/attendance_token.py` — AttendanceToken model (token, device_id, schedule_entry_id, lesson_date, is_active, expires_at)
- `app/models/attendance_record.py` — AttendanceRecord model (student_id, token_id, checked_in_at, unique on student+token)
- `app/models/user.py` — User model (role, class_name, is_active)
- `app/models/device.py` — Device model (room, label)
- `app/routers/admin.py` — Admin router pattern (Jinja2Templates, require_role, query patterns)
- `app/templates/admin_base.html` — Base template pattern to replicate for teacher_base.html
- `app/dependencies.py` — `require_role` dependency
- `.planning/phases/04-teacher-interface/04-UI-SPEC.md` — UI design contract (if exists)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/templates/admin_base.html` — pattern for teacher_base.html (nav, flash messages, block structure)
- `app/dependencies.py` — `require_role("teacher")` already tested in Phase 2
- `app/routers/admin.py` — pattern for router with Jinja2Templates and query params for flash messages
- `app/static/admin.js` — NOT needed for teacher pages (read-only, no inline editing)

### Established Patterns
- Jinja2Templates instantiated per-router
- German-language UI text
- Flash messages via `?msg=` and `?error=` query params
- Pico CSS classless styling — `<article>`, `<table>`, `<nav>` elements
- `require_role()` dependency returns User ORM object

### Integration Points
- `/teacher` redirect from login (auth.py line 75) — Phase 2 already routes teachers here
- ScheduleEntry.teacher_id FK → User.id — filter lessons by logged-in teacher
- AttendanceToken.schedule_entry_id + lesson_date — link tokens to specific lesson instances
- AttendanceRecord.token_id + student_id — determine who checked in

</code_context>

<specifics>
## Specific Ideas

- Table view for dashboard (not cards) — more compact, consistent with admin tables
- Full class roster with status in both attendance list and CSV — teacher sees who's absent
- Semicolon CSV separator for German Excel compatibility
- UTF-8 BOM for proper Umlaut display in Excel

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-teacher-interface*
*Context gathered: 2026-03-29*
