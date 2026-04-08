# Phase 14: CSV Import - Context

**Gathered:** 2026-04-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Bulk creation of users and schedule entries via template-based CSV upload with validation preview. Admin downloads a template, fills it in, uploads, sees a validation table, and confirms import. Two separate flows: user CSV and schedule CSV.

</domain>

<decisions>
## Implementation Decisions

### CSV Format & Templates
- **D-01:** Comma-delimited CSV (standard comma separator, not semicolons)
- **D-02:** User CSV template columns: `email, first_name, last_name, role, class_name, password` — password is plaintext in CSV, server hashes on import
- **D-03:** Schedule CSV references teachers by email and devices by device_id string (e.g. "e101") — human-readable, resolved to FK IDs on import
- **D-04:** Template download provides pre-filled header row with example data row (commented or as placeholder)

### Validation & Error Display
- **D-05:** Validation preview shows all rows in a Pico CSS table with red highlighting on invalid rows; error message in a last column per row
- **D-06:** All-or-nothing import — if any row has errors, nothing is committed. Admin must fix all errors and re-upload
- **D-07:** Schedule CSV validates for device+weekday+time overlaps (same logic as existing manual schedule form conflict check)

### Upload Flow & UI Placement
- **D-08:** CSV import sections embedded on existing admin pages — user import on /admin/users, schedule import on /admin/devices
- **D-09:** Two-step flow: Step 1 = file upload form, Step 2 = server parses and shows validation table with confirm/back buttons. Single page with form replacement (POST returns preview, second POST confirms)

### Edge Cases & Conflicts
- **D-10:** Duplicate emails trigger upsert — if email exists, update that user's fields (first_name, last_name, role, class_name, password) with CSV values
- **D-11:** Schedule overlap detection flags overlapping entries as errors (reuse existing conflict check logic from admin.js / admin router)

### Claude's Discretion
- **D-12:** Max CSV file size — Claude picks a reasonable limit for school prototype
- **D-13:** CSV encoding handling (UTF-8 with/without BOM detection)
- **D-14:** Template download format details (example row content, instructions)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — CSV-01 through CSV-06 define acceptance criteria

### Existing Patterns
- `app/routers/teacher.py` lines 278-318 — CSV export pattern (semicolons + UTF-8 BOM + `csv` module). Import should use `csv` module similarly
- `app/routers/admin.py` — User creation and schedule creation endpoints with validation logic to reuse
- `app/static/admin.js` — Schedule conflict checking via `/admin/api/schedule/check-conflict` endpoint

### Models
- `app/models/user.py` — User model fields (email, first_name, last_name, role, class_name, password_hash, is_active)
- `app/models/schedule_entry.py` — ScheduleEntry model fields (device_id, teacher_id, class_name, weekday, start_time, end_time, late_threshold_minutes)

### Templates
- `app/templates/admin_users.html` — Where user CSV import section will be added
- `app/templates/admin_devices.html` — Where schedule CSV import section will be added

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `csv` module already used in teacher.py for export — use for import parsing
- `get_password_hash()` from `app/services/auth.py` — hash plaintext passwords from CSV
- Admin router has user creation logic (email uniqueness check, role validation) — reuse validation
- Admin router has schedule creation logic with conflict checking — reuse for schedule CSV validation
- `SchoolClass` model auto-creates class entries — may need to handle new classes from CSV

### Established Patterns
- Admin pages use `admin_base.html` with Pico CSS semantic HTML
- Forms use POST with `RedirectResponse` + query param messages for success/error feedback
- Tables wrapped in `<figure>` for horizontal scroll on mobile
- `FastAPI Form()` for form data, will need `UploadFile` for CSV upload

### Integration Points
- New routes added to `app/routers/admin.py` (template download + upload + confirm endpoints)
- New sections added to `admin_users.html` and `admin_devices.html` templates
- Device lookup by `device_id` string (not integer PK) for schedule CSV resolution
- Teacher lookup by email for schedule CSV resolution

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 14-csv-import*
*Context gathered: 2026-04-08*
