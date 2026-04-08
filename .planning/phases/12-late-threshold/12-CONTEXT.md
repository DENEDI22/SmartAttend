# Phase 12: Late Threshold - Context

**Gathered:** 2026-04-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Three-state attendance model (Anwesend / Verspätet / Abwesend) with a configurable late threshold. Global default with per-schedule-entry override. Teacher roster and dashboard updated to show the third state.

</domain>

<decisions>
## Implementation Decisions

### Global default configuration
- **D-01:** Global default late threshold stored via a new `/admin/settings` page — runtime configurable, no restart needed
- **D-02:** Default value is 10 minutes
- **D-03:** Settings page is a simple form under admin nav — store the value in a new `SystemSetting` DB table (key-value) or as a single-row config table. Keep it simple.

### Per-entry override
- **D-04:** Add nullable `late_threshold_minutes` column to `ScheduleEntry` model (NULL = use global default)
- **D-05:** Optional number field labeled "Verspätung (Min.)" on the schedule create/edit form — empty means global default

### Late classification logic
- **D-06:** Classification: if `checked_in_at <= start_time + threshold` → "Anwesend", else → "Verspätet". No record → "Abwesend"
- **D-07:** Per-entry override wins over global default (NULL-means-default pattern)

### Teacher roster display
- **D-08:** Status text with color: "Anwesend" in green, "Verspätet" in orange/yellow, "Abwesend" in red — using Pico CSS semantic colors or inline styles
- **D-09:** Teacher dashboard shows late count alongside present and absent counts for each lesson

### CSV export
- **D-10:** CSV Status column shows three states: Anwesend / Verspätet / Abwesend (replaces previous two-state)

### Claude's Discretion
- Exact admin settings page layout and styling
- SystemSetting table design (single-row vs key-value)
- How to handle edge case where checked_in_at exactly equals the threshold cutoff
- Whether to show the threshold value on the teacher roster page

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements fully captured in decisions above

### Codebase references
- `app/models/schedule_entry.py` — ScheduleEntry model (add late_threshold_minutes column)
- `app/models/attendance_record.py` — AttendanceRecord with checked_in_at timestamp
- `app/routers/teacher.py` — `_build_roster()` function that classifies Anwesend/Abwesend (modify for third state)
- `app/routers/teacher.py` — Teacher dashboard route with attendance counts
- `app/config.py` — Settings class with pydantic-settings
- `app/routers/admin.py` — Admin routes (add settings page and schedule form field)
- `app/templates/admin_base.html` — Admin nav (add Einstellungen link)
- `app/templates/teacher_lesson.html` — Teacher lesson roster template (add Verspätet styling)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_build_roster()` in teacher.py already queries AttendanceRecord and classifies status — extend with threshold logic
- `ScheduleEntry.start_time` is a `time` object — combine with lesson date for threshold comparison
- Admin router pattern: form POST with redirect + query params for feedback

### Established Patterns
- Models use SQLAlchemy 2.0 Mapped[] columns
- Admin pages extend `admin_base.html` with `{% block admin_content %}`
- Schedule form uses expandable per-device sections with JSON conflict-check API
- Error/success feedback via `?msg=` and `?error=` query params

### Integration Points
- `_build_roster()` needs threshold parameter to classify Verspätet
- Teacher dashboard needs late count in addition to checked_in count
- Schedule create/edit forms need optional late_threshold_minutes field
- New admin settings page + nav link
- CSV export in teacher.py needs third status value

</code_context>

<specifics>
## Specific Ideas

- Keep the admin settings page minimal — just one field for now (late threshold), extensible for future settings
- Color coding should be obvious at a glance: green/orange/red

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 12-late-threshold*
*Context gathered: 2026-04-08*
