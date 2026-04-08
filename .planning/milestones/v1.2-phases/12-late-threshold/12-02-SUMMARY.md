---
phase: 12-late-threshold
plan: 02
subsystem: ui, api
tags: [fastapi, jinja2, pico-css, sqlalchemy]

requires:
  - phase: 12-late-threshold
    provides: SystemSetting model, late_threshold_minutes column on ScheduleEntry
provides:
  - Three-state attendance classification (Anwesend/Verspaetet/Abwesend) in teacher roster
  - Late count display in teacher dashboard
  - CSV export with three status values
affects: []

tech-stack:
  added: []
  patterns: [three-state classification with per-entry threshold override]

key-files:
  created: []
  modified: [app/routers/teacher.py, app/templates/teacher_lesson.html, app/templates/teacher_dashboard.html]

key-decisions:
  - "Verspaetet students count toward checked_in total (they did attend, just late)"
  - "Global threshold cached once per dashboard request to avoid repeated DB lookups"

patterns-established:
  - "Three-color status: green #2e7d32 Anwesend, orange #e65100 Verspaetet, red pico-del-color Abwesend"

requirements-completed: [LATE-03, LATE-04]

duration: 3min
completed: 2026-04-08
---

# Phase 12 Plan 02: Late Classification in Teacher Views Summary

**Three-state attendance display (Anwesend/Verspaetet/Abwesend) with color-coded roster, dashboard late counts, and CSV export**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-08T08:42:03Z
- **Completed:** 2026-04-08T09:01:04Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- _build_roster now classifies students into three states using per-entry or global late threshold
- Teacher lesson roster displays green/orange/red color-coded statuses with late count in summary
- Teacher dashboard shows inline late count per lesson
- CSV export automatically includes Verspaetet as third status value

## Task Commits

Each task was committed atomically:

1. **Task 1: Add late classification to _build_roster and dashboard counts** - `fa1dc26` (feat)
2. **Task 2: Update teacher templates for three-state display** - `b82e847` (feat)

## Files Created/Modified
- `app/routers/teacher.py` - Three-state classification in _build_roster, late counts in dashboard query
- `app/templates/teacher_lesson.html` - Color-coded status cells, late count in summary line
- `app/templates/teacher_dashboard.html` - Inline late count display next to attendance figures

## Decisions Made
- Verspaetet students are included in checked_in count since they did attend
- Global threshold is read once before the dashboard loop for efficiency

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Late threshold feature complete across data layer, classification logic, and UI
- Phase 12 fully delivered: admin settings, per-entry overrides, three-state teacher views

---
*Phase: 12-late-threshold*
*Completed: 2026-04-08*
