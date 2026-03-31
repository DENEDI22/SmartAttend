# Phase 3: Admin Interface - Context

**Gathered:** 2026-03-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Admin can manage devices, users, and the timetable through a web UI. Three CRUD sections: devices (with integrated per-device schedule), users, and a class list. All UI in German, using Pico CSS classless styling served from static/.

</domain>

<decisions>
## Implementation Decisions

### Page Structure & Navigation
- **D-01:** Two separate pages: `/admin/devices` (devices + per-device schedule) and `/admin/users` (user management). Devices and schedule are combined because schedules are logically tied to devices.
- **D-02:** Shared nav bar on both pages: SmartAttend brand on left, Geräte + Benutzer links, Abmelden button on right. Nav extends base.html via a block.
- **D-03:** Logout button in nav posts to `/auth/logout` (existing endpoint from Phase 2).

### Device Table & Interactions
- **D-04:** Device table columns: Gerät-ID, Raum, Label, Status (Online/Offline), Aktiv (Ja/Nein), Aktionen (An/Aus toggle).
- **D-05:** Room and Label fields are editable directly in the table rows (inline editing). "Änderungen speichern" and "Zurücksetzen" buttons below the table, only active when unsaved changes exist. Requires JS for change detection.
- **D-06:** Enable/disable toggle is a separate action button per row (not part of the bulk save). Toggles `is_enabled` immediately via POST.
- **D-07:** Expandable rows via `<details>` element: clicking a device row expands to show its schedule entries below, with an "Eintrag hinzufügen" form.

### User Table & Interactions
- **D-08:** User table columns: Name (Vor+Nachname), E-Mail, Rolle, Klasse, Status (Aktiv/Inaktiv), Aktionen (Deaktivieren).
- **D-09:** Name (first + last), class, and role fields are editable directly in the table rows (same inline-edit pattern as devices). "Änderungen speichern" and "Zurücksetzen" buttons below the table, only active when unsaved changes exist.
- **D-10:** Deactivate button per row: sets `is_active=False` (soft delete). Uses `confirm('Benutzer deaktivieren?')` dialog. Deactivated users remain visible in the table with "Inaktiv" status.
- **D-11:** "Neuer Benutzer" form below the user table in an `<article>` card. Fields: Vorname, Nachname, E-Mail, Passwort, Rolle (dropdown: Admin/Lehrer/Schüler), Klasse (dropdown from SchoolClass table with option to type new). Submit creates user and reloads page.

### Class Management
- **D-12:** New `SchoolClass` model: `id` (int PK), `name` (str, unique). Single source of truth for class names.
- **D-13:** `User.class_name` and `ScheduleEntry.class_name` become FK references to SchoolClass. Migration: existing string values become SchoolClass rows.
- **D-14:** Class dropdown in user form and schedule form populated from SchoolClass table. Admin can type a new class name which auto-creates a SchoolClass row.

### Schedule Management (within Device page)
- **D-15:** Schedule entries shown per device in expandable `<details>` sections. Columns: Klasse, Lehrer, Tag, Zeitraum, Löschen-Button.
- **D-16:** "Eintrag hinzufügen" form within each device's expanded section. Fields: Klasse (dropdown), Lehrer (dropdown of teachers), Tag (dropdown Mo-So), Startzeit, Endzeit.
- **D-17:** Inline JS validation for schedule conflicts: checks via API endpoint (`GET /api/schedule/check-conflict`) as form is filled. "Hinzufügen" button disabled until validation passes. Error message: "Zeitkonflikt: Gerät ist bereits belegt am [Tag] [Zeit] (Klasse [X])."
- **D-18:** Delete schedule entry uses `confirm('Eintrag löschen?')` browser dialog before submitting.

### Claude's Discretion
- Exact JS implementation for inline edit change detection and save/revert logic
- Exact structure of the conflict-check API endpoint
- Template file naming and Jinja2 block structure
- Flash message styling for success/error feedback
- How the "new class" option integrates into the dropdown (HTML datalist, select+input combo, etc.)
- Empty states for tables when no devices/users/entries exist

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements fully captured in decisions above and REQUIREMENTS.md (ADMIN-01 through ADMIN-10).

### Codebase References
- `app/models/device.py` — Device model fields (device_id, room, label, is_enabled, is_online, last_seen, last_lux)
- `app/models/user.py` — User model fields (email, first_name, last_name, role, class_name, password_hash, is_active)
- `app/models/schedule_entry.py` — ScheduleEntry model fields (device_id FK, teacher_id FK, class_name, weekday, start_time, end_time)
- `app/routers/auth.py` — Auth router pattern (Jinja2Templates instantiation, role-based redirects, logout endpoint)
- `app/dependencies.py` — `get_current_user` and `require_role` dependencies
- `app/templates/base.html` — Base template with `<main class="container">` layout
- `app/templates/login.html` — Existing German-language template pattern with error flash
- `.planning/phases/03-admin-interface/03-UI-SPEC.md` — UI design contract (spacing, typography, color, copywriting specs)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/templates/base.html` — extends with nav block for admin pages
- `app/services/auth.py` — password hashing via passlib for user creation
- `app/dependencies.py` — `require_role("admin")` for protecting all admin routes
- `app/routers/auth.py` — pattern for Jinja2Templates usage in routers

### Established Patterns
- Jinja2Templates instantiated per-router (not globally)
- German-language UI text (error messages, labels)
- HTTP-only cookie auth with 303 redirects for unauthenticated access
- Pico CSS classless styling — semantic HTML elements, no custom CSS classes needed
- SQLAlchemy 2.0 `Mapped[]` typed columns pattern

### Integration Points
- `/admin` redirect from login (auth.py line 73) — currently 404, Phase 3 creates this route
- `require_role("admin")` — already tested in Phase 2 integration tests
- Device, User, ScheduleEntry models — all exist from Phase 1, read/write via SQLAlchemy sessions

</code_context>

<specifics>
## Specific Ideas

- Devices and Schedule on the same page because "these two functions are logically tightly tied — schedule should be defined for each device"
- Tables with inline-editable fields (not separate edit pages/forms) — save+revert buttons below, active only when changes exist
- Class names as a dedicated SchoolClass model with dropdown + add-new capability
- Schedule conflict validation happens inline (before submit) via API, not after submit as a flash message

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-admin-interface*
*Context gathered: 2026-03-29*
