# Phase 13: Student Dashboard - Context

**Gathered:** 2026-04-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Students can see their own attendance history with summary statistics and per-lesson detail. This phase adds a student dashboard page showing attendance stats (card grid) and a chronological lesson list grouped by month.

</domain>

<decisions>
## Implementation Decisions

### Summary Statistics Layout
- **D-01:** Summary stats displayed as a card grid using Pico CSS `<article>` elements in a CSS grid layout
- **D-02:** All 5 stat cards equal weight — no hero/prominent card. Stats: total lessons, attended, missed, late, attendance percentage
- **D-03:** Late count gets its own dedicated card (not folded into Anwesend as a sub-note)

### Lesson List Scope & Structure
- **D-04:** Lesson list shows the last 12 months of history
- **D-05:** Lessons grouped by month with a heading per month (e.g. "April 2026", "Maerz 2026") and a table per group, newest first

### Claude's Discretion
- Status display and color coding for Anwesend/Verspaetet/Abwesend — use an approach consistent with the teacher dashboard's existing pattern

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements fully captured in decisions above and REQUIREMENTS.md.

### Requirements
- `.planning/REQUIREMENTS.md` — STUD-01 (summary stats), STUD-02 (detailed lesson list)

### Existing Patterns
- `app/templates/teacher_dashboard.html` — Table layout pattern, late count display, Pico CSS conventions
- `app/templates/teacher_lesson.html` — Per-lesson detail pattern with three-state attendance
- `app/templates/student.html` — Current student page (to be extended/replaced)
- `app/templates/student_base.html` — Student layout base template
- `app/models/attendance_record.py` — AttendanceRecord model (student_id, token_id, checked_in_at)
- `app/models/attendance_token.py` — AttendanceToken model (schedule_entry_id, lesson_date, device_id)
- `app/models/schedule_entry.py` — ScheduleEntry model (class_name, weekday, times, late_threshold_minutes)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `student_base.html`: Layout base for student pages — already extends `base.html` with student nav
- `_password_change.html`: Password change partial — already included in current student.html
- Teacher dashboard query pattern: joins ScheduleEntry + AttendanceToken + AttendanceRecord for lesson data

### Established Patterns
- Pico CSS `<figure><table>` for data tables (teacher dashboard)
- Three-state attendance: Anwesend / Verspaetet / Abwesend — classification logic in teacher router
- Late threshold resolution: per-entry override or global default via SystemSetting
- German UI strings throughout all templates

### Integration Points
- No student router exists yet — needs new `app/routers/student.py`
- Student role already exists in auth system (JWT role-based access)
- `student.html` currently minimal — will be replaced with dashboard content
- Main app (`app/main.py`) needs to register the new student router

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches for card grid and grouped table rendering within Pico CSS constraints.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 13-student-dashboard*
*Context gathered: 2026-04-08*
