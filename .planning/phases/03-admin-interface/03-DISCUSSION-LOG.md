# Phase 3: Admin Interface - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-29
**Phase:** 03-admin-interface
**Areas discussed:** Page structure & navigation, Table interactions, Form placement & flow, Schedule conflict feedback

---

## Page Structure & Navigation

| Option | Description | Selected |
|--------|-------------|----------|
| Tabbed single page | One /admin page with 3 tabs via Pico CSS nav | |
| Separate pages | Three routes: /admin/devices, /admin/users, /admin/schedule | ✓ (modified) |
| You decide | Let Claude pick | |

**User's choice:** Separate pages, BUT combine devices and schedule into one page because they are logically tightly tied. Schedule should be defined for each device.
**Notes:** Final structure: `/admin/devices` (devices + per-device schedule) and `/admin/users`.

### Follow-up: Device + Schedule integration

| Option | Description | Selected |
|--------|-------------|----------|
| Expandable row | Click device row to expand schedule below. Uses `<details>` element. | ✓ |
| Separate detail page | /admin/devices/3 shows device info + schedule | |
| You decide | Let Claude pick | |

**User's choice:** Expandable row with schedule per device.

### Follow-up: Nav bar

| Option | Description | Selected |
|--------|-------------|----------|
| Shared nav with logout | Nav bar with Geräte + Benutzer + Abmelden | ✓ |
| Nav without logout | Nav for section switching only | |
| You decide | Let Claude pick | |

**User's choice:** Shared nav with logout.

---

## Table Interactions

### Device editing

| Option | Description | Selected |
|--------|-------------|----------|
| Inline form in expanded row | Edit fields in expanded device section | |
| Action buttons in table row | Table row shows info, buttons for edit + enable/disable | ✓ (modified) |
| You decide | Let Claude pick | |

**User's choice:** Initially selected action buttons, then revised: fields should be editable directly in the table (inline editing), with save/revert buttons below the table, active only when changes exist. Same pattern as users.

### User table

| Option | Description | Selected |
|--------|-------------|----------|
| Table with deactivate button | Simple read-only table, deactivate per row | |
| Table with edit + deactivate | Table with both edit and deactivate capabilities | ✓ (modified) |
| You decide | Let Claude pick | |

**User's choice:** Table with edit + deactivate. Clarified: no separate "Bearbeiten" button — make fields editable directly in the table with save/revert buttons below, active only when unsaved changes exist. Class and name should be editable.

---

## Form Placement & Flow

### User creation form

| Option | Description | Selected |
|--------|-------------|----------|
| Below the table | Form in article card below user table, always visible | ✓ |
| Separate create page | /admin/users/new with its own template | |
| You decide | Let Claude pick | |

**User's choice:** Below the table.

### Edit flow

| Option | Description | Selected |
|--------|-------------|----------|
| Same form below, pre-filled | Create form transforms into edit form | ✓ (superseded) |
| Separate edit page | /admin/users/5/edit | |
| You decide | Let Claude pick | |

**User's choice:** Initially selected same form below, then revised the entire approach: no separate edit form at all. Fields are editable directly in the table rows (inline editing).

### Device edit pattern consistency

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, same pattern | Device table also has inline-editable fields | ✓ |
| No, different pattern | Devices use action buttons | |
| You decide | Let Claude pick | |

**User's choice:** Yes, same inline-editable pattern for devices.

---

## Schedule Conflict Feedback

### Conflict display

| Option | Description | Selected |
|--------|-------------|----------|
| Flash message after submit | Server rejects POST, re-renders with red alert | |
| Inline validation before submit | Check conflicts via JS/AJAX as form is filled | ✓ |
| You decide | Let Claude pick | |

**User's choice:** Inline validation before submit. Also: "Apply Changes" button disabled until validation passes.

### Schedule deletion

| Option | Description | Selected |
|--------|-------------|----------|
| Browser confirm() dialog | JS confirm before delete | ✓ |
| No confirmation | Delete immediately | |
| You decide | Let Claude pick | |

**User's choice:** Browser confirm() dialog.

---

## Additional: Class Management

| Option | Description | Selected |
|--------|-------------|----------|
| Dedicated table | New SchoolClass model, FK references | ✓ |
| Derived from existing data | No table, DISTINCT query from users+schedule | |
| You decide | Let Claude pick | |

**User's choice:** Dedicated SchoolClass table. Classes saved in a list, admin can choose from dropdown OR add a new class.
**Notes:** User initiated this topic: "Classes should be saved in a list so that when assigning a student to a class, the admin can choose from a dropdown OR add a new class which will appear in the list later."

---

## Claude's Discretion

- Exact JS implementation for inline edit change detection
- Structure of conflict-check API endpoint
- Template file naming and Jinja2 block structure
- Flash message styling
- "New class" dropdown integration mechanism
- Empty states for tables

## Deferred Ideas

None — discussion stayed within phase scope.
