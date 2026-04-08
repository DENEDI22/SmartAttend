---
phase: 12-late-threshold
plan: 01
subsystem: database, ui
tags: [sqlalchemy, fastapi, jinja2, pico-css]

requires:
  - phase: 04-admin-ui
    provides: Admin router, admin_base.html, device/schedule CRUD
provides:
  - SystemSetting key-value model for global configuration
  - Nullable late_threshold_minutes column on ScheduleEntry
  - Admin settings page at /admin/settings
  - Per-entry late threshold field in schedule form
affects: [12-02-late-classification]

tech-stack:
  added: []
  patterns: [key-value settings model with get_value/set_value class methods]

key-files:
  created: [app/models/system_setting.py, app/templates/admin_settings.html]
  modified: [app/models/schedule_entry.py, app/models/__init__.py, app/routers/admin.py, app/templates/admin_base.html, app/templates/admin_devices.html]

key-decisions:
  - "SystemSetting uses key-value pattern with string values for flexibility"
  - "Form sends late_threshold_minutes as string to handle empty input gracefully"

patterns-established:
  - "Key-value settings: SystemSetting.get_value(db, key, default) / .set_value(db, key, value)"

requirements-completed: [LATE-01, LATE-02]

duration: 4min
completed: 2026-04-08
---

# Phase 12 Plan 01: Late Threshold Data Layer and Admin UI Summary

**SystemSetting key-value model and admin settings page for configuring global/per-entry late thresholds**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-08T12:35:30Z
- **Completed:** 2026-04-08T12:39:18Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Created SystemSetting model with get_value/set_value class methods for persistent key-value storage
- Added nullable late_threshold_minutes column to ScheduleEntry for per-entry overrides
- Built admin settings page at /admin/settings with global late threshold form (default: 10 min)
- Added optional late threshold field to schedule entry form with "Standard" display for NULL values

## Task Commits

Each task was committed atomically:

1. **Task 1: Create SystemSetting model, add ScheduleEntry column, wire imports** - `9943cfe` (feat)
2. **Task 2: Add admin settings page and schedule form late threshold field** - `ef493ae` (feat)

## Files Created/Modified
- `app/models/system_setting.py` - Key-value settings model with get_value/set_value helpers
- `app/models/schedule_entry.py` - Added nullable late_threshold_minutes column
- `app/models/__init__.py` - Wired SystemSetting import
- `app/routers/admin.py` - Added GET/POST /admin/settings routes and late_threshold_minutes to schedule_add
- `app/templates/admin_settings.html` - Admin settings page with late threshold form
- `app/templates/admin_base.html` - Added Einstellungen nav link
- `app/templates/admin_devices.html` - Added late threshold column and form field

## Decisions Made
- SystemSetting uses string values for all settings (converted at usage site) for flexibility
- Form parameter for late_threshold_minutes accepted as string to handle empty input from HTML forms

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- SystemSetting model and ScheduleEntry column ready for Plan 02 late classification logic
- Global default retrievable via `SystemSetting.get_value(db, "late_threshold_minutes", "10")`
- Per-entry override available via `entry.late_threshold_minutes` (NULL = use global)

---
*Phase: 12-late-threshold*
*Completed: 2026-04-08*
