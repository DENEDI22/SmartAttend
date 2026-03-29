# Phase 3: Admin Interface - Research

**Researched:** 2026-03-29
**Domain:** FastAPI + Jinja2 + Pico CSS admin CRUD UI
**Confidence:** HIGH

## Summary

Phase 3 builds a server-rendered admin interface with two pages: Devices (with embedded per-device schedule) and Users. The stack is entirely established from Phases 1-2: FastAPI routers, Jinja2 templates extending `base.html`, Pico CSS v2.1.1 classless styling, SQLAlchemy 2.0 ORM queries, and cookie-based auth with `require_role("admin")`. No new Python packages are needed.

The primary technical challenges are: (1) a new `SchoolClass` model with FK migration from string `class_name` fields, (2) schedule overlap detection in SQLAlchemy for SQLite (no native OVERLAPS operator), (3) inline-editable table rows with JS change detection (the first real JavaScript in the project), and (4) a conflict-check API endpoint for async schedule validation.

**Primary recommendation:** Structure as three waves -- Wave 1: SchoolClass model + admin router skeleton + device page, Wave 2: user management page, Wave 3: schedule CRUD with conflict detection. Keep JS minimal and vanilla (no build step).

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Two separate pages: `/admin/devices` (devices + per-device schedule) and `/admin/users` (user management). Devices and schedule are combined because schedules are logically tied to devices.
- **D-02:** Shared nav bar on both pages: SmartAttend brand on left, Geraete + Benutzer links, Abmelden button on right. Nav extends base.html via a block.
- **D-03:** Logout button in nav posts to `/auth/logout` (existing endpoint from Phase 2).
- **D-04:** Device table columns: Geraet-ID, Raum, Label, Status (Online/Offline), Aktiv (Ja/Nein), Aktionen (An/Aus toggle).
- **D-05:** Room and Label fields are editable directly in the table rows (inline editing). "Aenderungen speichern" and "Zuruecksetzen" buttons below the table, only active when unsaved changes exist. Requires JS for change detection.
- **D-06:** Enable/disable toggle is a separate action button per row (not part of the bulk save). Toggles `is_enabled` immediately via POST.
- **D-07:** Expandable rows via `<details>` element: clicking a device row expands to show its schedule entries below, with an "Eintrag hinzufuegen" form.
- **D-08:** User table columns: Name (Vor+Nachname), E-Mail, Rolle, Klasse, Status (Aktiv/Inaktiv), Aktionen (Deaktivieren).
- **D-09:** Name (first + last), class, and role fields are editable directly in the table rows (same inline-edit pattern as devices). "Aenderungen speichern" and "Zuruecksetzen" buttons below the table, only active when changes exist.
- **D-10:** Deactivate button per row: sets `is_active=False` (soft delete). Uses `confirm('Benutzer deaktivieren?')` dialog. Deactivated users remain visible with "Inaktiv" status.
- **D-11:** "Neuer Benutzer" form below the user table in an `<article>` card. Fields: Vorname, Nachname, E-Mail, Passwort, Rolle (dropdown), Klasse (dropdown from SchoolClass with option to type new).
- **D-12:** New `SchoolClass` model: `id` (int PK), `name` (str, unique). Single source of truth for class names.
- **D-13:** `User.class_name` and `ScheduleEntry.class_name` become FK references to SchoolClass. Migration: existing string values become SchoolClass rows.
- **D-14:** Class dropdown in user form and schedule form populated from SchoolClass table. Admin can type a new class name which auto-creates a SchoolClass row.
- **D-15:** Schedule entries shown per device in expandable `<details>` sections. Columns: Klasse, Lehrer, Tag, Zeitraum, Loeschen-Button.
- **D-16:** "Eintrag hinzufuegen" form within each device's expanded section. Fields: Klasse (dropdown), Lehrer (dropdown of teachers), Tag (dropdown Mo-So), Startzeit, Endzeit.
- **D-17:** Inline JS validation for schedule conflicts via API endpoint (`GET /api/schedule/check-conflict`). "Hinzufuegen" button disabled until validation passes.
- **D-18:** Delete schedule entry uses `confirm('Eintrag loeschen?')` browser dialog before submitting.

### Claude's Discretion
- Exact JS implementation for inline edit change detection and save/revert logic
- Exact structure of the conflict-check API endpoint
- Template file naming and Jinja2 block structure
- Flash message styling for success/error feedback
- How the "new class" option integrates into the dropdown (HTML datalist, select+input combo, etc.)
- Empty states for tables when no devices/users/entries exist

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ADMIN-01 | Admin can view all registered devices with status | Device table on `/admin/devices` with is_online/is_enabled/last_seen/last_lux columns |
| ADMIN-02 | Admin can assign a device to a room and give it a label | Inline-editable room/label fields with bulk save via POST |
| ADMIN-03 | Admin can enable/disable a device | Per-row toggle button, immediate POST to `/admin/devices/{id}/toggle` |
| ADMIN-04 | Admin can view all users | User table on `/admin/users` with name/role/class columns |
| ADMIN-05 | Admin can create a new user | "Neuer Benutzer" form below user table, POST creates user with hashed password |
| ADMIN-06 | Admin can deactivate a user (soft delete) | Deactivate button per row, sets is_active=False, confirm() dialog |
| ADMIN-07 | Admin can view the full timetable across all devices | Schedule entries shown per-device in expandable `<details>` sections |
| ADMIN-08 | Admin can add a schedule entry | "Eintrag hinzufuegen" form per device, POST creates ScheduleEntry |
| ADMIN-09 | Admin cannot add conflicting schedule entry | Overlap detection query in Python + JS conflict-check API endpoint |
| ADMIN-10 | Admin can delete a schedule entry | Delete button per entry, confirm() dialog, POST deletes row |

</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Tech Stack:** FastAPI + Jinja2 + SQLAlchemy + SQLite + Pico CSS (all already installed)
- **CSS:** Pico CSS served locally from `static/` -- no CDN, no JS builds
- **Database:** SQLite (no native OVERLAPS operator, must use Python-side overlap logic)
- **Hardware:** No ESP32 -- dummy clients only (irrelevant to this phase)
- **GSD Workflow:** All changes through GSD commands

## Standard Stack

### Core (already installed, no new packages)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.135.2 | Router + API endpoints | Already in requirements.txt |
| Jinja2 | 3.1.6 | Server-side HTML templates | Already in requirements.txt |
| SQLAlchemy | 2.0.48 | ORM queries for CRUD | Already in requirements.txt |
| Pico CSS | 2.1.1 | Classless CSS framework | Already in `app/static/pico.min.css` |
| passlib[bcrypt] | 1.7.4 + bcrypt 3.2.2 | Password hashing for user creation | Already in requirements.txt |

### Supporting (no new installs needed)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-multipart | 0.0.22 | Form data parsing | Already installed, needed for Form() params |
| pytest | 8.4.2 | Testing | Already installed for test suite |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Query params for flash messages | Starlette SessionMiddleware | Session adds complexity + secret key management; query params are simpler for this use case |
| `<datalist>` for class dropdown | `<select>` + separate text input | Datalist allows typing + autocomplete natively, simpler than JS combo box |
| Vanilla JS for inline editing | HTMX | HTMX adds a dependency; vanilla JS is sufficient for change detection |

**Installation:** No new packages needed. All dependencies already in `requirements.txt`.

## Architecture Patterns

### Recommended Project Structure
```
app/
├── models/
│   ├── school_class.py      # NEW: SchoolClass model
│   ├── device.py             # EXISTING (unchanged)
│   ├── user.py               # MODIFY: class_name FK to SchoolClass
│   └── schedule_entry.py     # MODIFY: class_name FK to SchoolClass
├── routers/
│   ├── auth.py               # EXISTING (unchanged)
│   └── admin.py              # NEW: all admin routes
├── templates/
│   ├── base.html             # MODIFY: add nav block
│   ├── admin_base.html       # NEW: extends base, adds admin nav
│   ├── admin_devices.html    # NEW: device table + schedule sections
│   └── admin_users.html      # NEW: user table + create form
├── static/
│   ├── pico.min.css          # EXISTING
│   └── admin.js              # NEW: inline edit change detection + conflict check
└── main.py                   # MODIFY: register admin router
```

### Pattern 1: Admin Router with require_role
**What:** Single `admin.py` router file with all admin routes, protected by `require_role("admin")`
**When to use:** All admin page routes and API endpoints
**Example:**
```python
# Source: Established pattern from app/routers/auth.py
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/devices")
async def devices_page(
    request: Request,
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    devices = db.query(Device).all()
    # ...
    return templates.TemplateResponse(
        request=request,
        name="admin_devices.html",
        context={"devices": devices, "user": user},
    )
```

### Pattern 2: Template Inheritance with Admin Nav
**What:** Three-level template hierarchy: base.html -> admin_base.html -> page templates
**When to use:** All admin pages share the same nav bar
**Example:**
```html
<!-- admin_base.html -->
{% extends "base.html" %}
{% block content %}
<nav>
  <ul>
    <li><strong>SmartAttend</strong></li>
  </ul>
  <ul>
    <li><a href="/admin/devices" {% if active_page == 'devices' %}aria-current="page"{% endif %}>Geraete</a></li>
    <li><a href="/admin/users" {% if active_page == 'users' %}aria-current="page"{% endif %}>Benutzer</a></li>
    <li>
      <form method="post" action="/auth/logout" style="margin: 0;">
        <button type="submit" class="outline secondary" style="margin: 0; padding: 0.5rem 1rem;">Abmelden</button>
      </form>
    </li>
  </ul>
</nav>
{% block admin_content %}{% endblock %}
{% endblock %}
```

### Pattern 3: Flash Messages via Query Parameters
**What:** Pass success/error messages via URL query params after redirect, render in template
**When to use:** After POST actions (create, update, delete, toggle) that redirect back to the page
**Example:**
```python
# In router:
return RedirectResponse(url="/admin/devices?msg=Erfolgreich+aktualisiert.", status_code=303)

# In template:
{% if request.query_params.get('msg') %}
<p role="alert" style="color: #2e7d32">{{ request.query_params.get('msg') }}</p>
{% endif %}
{% if request.query_params.get('error') %}
<p role="alert" style="color: var(--pico-del-color)">{{ request.query_params.get('error') }}</p>
{% endif %}
```

### Pattern 4: Inline Editable Table with Vanilla JS
**What:** Table cells contain `<input>` elements inside a `<form>`. JS tracks changes and enables/disables save/reset buttons.
**When to use:** Device room/label editing, user name/class/role editing
**Example:**
```html
<form method="post" action="/admin/devices/update" id="device-form">
  <figure>
    <table>
      <thead><tr><th>Geraet-ID</th><th>Raum</th><th>Label</th>...</tr></thead>
      <tbody>
        {% for device in devices %}
        <tr>
          <td>{{ device.device_id }}</td>
          <td><input type="text" name="room_{{ device.id }}" value="{{ device.room or '' }}" data-original="{{ device.room or '' }}"></td>
          <td><input type="text" name="label_{{ device.id }}" value="{{ device.label or '' }}" data-original="{{ device.label or '' }}"></td>
          ...
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </figure>
  <button type="submit" id="save-btn" disabled>Aenderungen speichern</button>
  <button type="button" id="reset-btn" disabled onclick="resetForm()">Zuruecksetzen</button>
</form>
```

### Pattern 5: Schedule Overlap Detection (SQLite-compatible)
**What:** Python-side overlap query since SQLite lacks OVERLAPS operator
**When to use:** Before inserting a new ScheduleEntry; also in the conflict-check API
**Example:**
```python
# Two time ranges [s1, e1) and [s2, e2) overlap iff s1 < e2 AND s2 < e1
def check_schedule_conflict(
    db: Session, device_id: int, weekday: int,
    start_time: time, end_time: time, exclude_id: int | None = None
) -> ScheduleEntry | None:
    query = db.query(ScheduleEntry).filter(
        ScheduleEntry.device_id == device_id,
        ScheduleEntry.weekday == weekday,
        ScheduleEntry.start_time < end_time,
        ScheduleEntry.end_time > start_time,
    )
    if exclude_id:
        query = query.filter(ScheduleEntry.id != exclude_id)
    return query.first()
```

### Pattern 6: Expandable Device Rows with `<details>`
**What:** Each device row wraps its schedule in a `<details>` element below the main table, or uses a secondary table row
**When to use:** D-07 requires expandable rows showing per-device schedule
**Example:**
```html
{% for device in devices %}
<details>
  <summary>
    <!-- Device row info rendered as a grid or flex layout -->
    {{ device.device_id }} | {{ device.room }} | ...
  </summary>
  <figure>
    <table>
      <thead><tr><th>Klasse</th><th>Lehrer</th><th>Tag</th><th>Zeitraum</th><th></th></tr></thead>
      <tbody>
        {% for entry in device.schedule_entries %}
        <tr>
          <td>{{ entry.class_name }}</td>
          <td>{{ entry.teacher_name }}</td>
          <td>{{ weekday_names[entry.weekday] }}</td>
          <td>{{ entry.start_time.strftime('%H:%M') }} - {{ entry.end_time.strftime('%H:%M') }}</td>
          <td>
            <form method="post" action="/admin/schedule/{{ entry.id }}/delete"
                  onsubmit="return confirm('Eintrag loeschen?')">
              <button type="submit" class="outline secondary">Loeschen</button>
            </form>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </figure>
  <!-- Add entry form for this device -->
  <form method="post" action="/admin/schedule/add">
    <input type="hidden" name="device_id" value="{{ device.id }}">
    ...
  </form>
</details>
{% endfor %}
```

### Anti-Patterns to Avoid
- **Separate edit pages per entity:** Decisions require inline editing in tables, not separate form pages
- **Global Jinja2Templates instance:** Project pattern is to instantiate per-router (`templates = Jinja2Templates(directory="app/templates")`)
- **JavaScript fetch() for form submissions:** All form submissions use standard POST with page reload; only the conflict-check endpoint uses fetch()
- **Custom CSS classes:** Pico CSS is classless -- use semantic HTML elements, not `.btn-primary` etc.
- **Hard deletes for users:** D-10 requires soft delete (is_active=False), not DELETE from database

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Password hashing | Custom bcrypt calls | `app.services.auth.get_password_hash()` | Already exists, handles truncation |
| Auth protection | Manual cookie checking | `require_role("admin")` dependency | Already tested in Phase 2 |
| CSS styling | Custom stylesheets | Pico CSS semantic HTML elements | Project constraint: classless CSS |
| Form parsing | Manual request body parsing | FastAPI `Form()` parameters | Built-in, type-safe |
| Time overlap logic | SQL OVERLAPS (SQLite lacks it) | Python-side query with `start < end AND end > start` | SQLite compatible |

## Common Pitfalls

### Pitfall 1: SchoolClass FK Migration Breaks Existing Data
**What goes wrong:** Adding a ForeignKey from `User.class_name` to `SchoolClass.name` requires existing class_name values to exist in the SchoolClass table first.
**Why it happens:** SQLAlchemy `create_all` creates tables but does not migrate data. If User rows already have `class_name="10A"`, a FK constraint will fail unless SchoolClass("10A") exists.
**How to avoid:** Since this is a prototype using `create_all()` (not Alembic migrations), the simplest approach is: (1) make the FK reference nullable and optional, (2) add a startup seed that ensures SchoolClass rows exist for any orphaned class_name values, or (3) change the FK to reference SchoolClass.id instead of SchoolClass.name and store `school_class_id` as an integer FK.
**Warning signs:** IntegrityError on startup after schema change.

### Pitfall 2: Inline Edit Form Conflicts with Toggle Forms
**What goes wrong:** The device table has both an inline-edit form (for room/label bulk save) and per-row toggle forms (for enable/disable). Nested forms are invalid HTML.
**Why it happens:** D-05 says room/label fields are in the table, and D-06 says toggle is per-row. If both are `<form>` elements, they cannot nest.
**How to avoid:** The toggle button should be its own small `<form>` inside its `<td>`, while the inline-edit inputs are `<input>` elements tracked by JS. The bulk save collects all input values via JS and submits via a separate form or fetch(). Alternatively, the bulk save form wraps the entire table and the toggle forms sit outside (each in their own `<td>` cell -- browsers allow a `<form>` per `<td>` cell if the cell contains only that form).
**Warning signs:** Toggle clicks triggering bulk save instead.

### Pitfall 3: `<details>` Inside `<table>` is Invalid HTML
**What goes wrong:** Putting `<details>` inside `<tbody>` rows is not valid HTML. Browsers may render it incorrectly.
**Why it happens:** D-07 says "expandable rows via `<details>`" but tables have strict element nesting rules.
**How to avoid:** Use `<details>` elements OUTSIDE the table, one per device. Each `<details>` contains the device summary info and its schedule table. This means the device list is not a single `<table>` but a series of `<details>` blocks (or use a card-based layout per device). Alternatively, use a device card approach: each device is an `<article>` with a `<details>` for its schedule.
**Warning signs:** Browser rendering quirks, missing expand/collapse behavior.

### Pitfall 4: Redirect After POST Returns 307 Instead of 303
**What goes wrong:** Using `RedirectResponse(url=..., status_code=302)` can cause browsers to re-POST to the redirect target.
**Why it happens:** HTTP 302 behavior is ambiguous. POST-redirect-GET requires 303.
**How to avoid:** Always use `status_code=303` for redirects after POST, matching the established Phase 2 pattern.
**Warning signs:** Form re-submission warnings in browser.

### Pitfall 5: `var(--del-color)` vs `var(--pico-del-color)`
**What goes wrong:** The existing `login.html` uses `var(--del-color)` (line 17), but Pico CSS v2 custom properties use the `--pico-` prefix.
**Why it happens:** Possible Pico v1 vs v2 difference, or login.html has a bug.
**How to avoid:** Use `var(--pico-del-color)` consistently in new templates, as specified in the UI spec.
**Warning signs:** Error text not showing red color.

### Pitfall 6: SQLAlchemy Session Not Committed After Bulk Update
**What goes wrong:** Updating multiple device room/label values in a loop without `db.commit()` loses all changes.
**Why it happens:** SQLAlchemy sessions auto-flush but do not auto-commit.
**How to avoid:** Always call `db.commit()` after the update loop. Use `try/except` to `db.rollback()` on error.
**Warning signs:** "Saved" message appears but values revert on page reload.

## Code Examples

### SchoolClass Model
```python
# Source: Follows established pattern from app/models/device.py
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class SchoolClass(Base):
    __tablename__ = "school_classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
```

### Conflict Check API Endpoint
```python
# Source: Discretion area -- recommended structure
from datetime import time
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import require_role
from app.models.schedule_entry import ScheduleEntry
from app.models.user import User


@router.get("/api/schedule/check-conflict")
async def check_conflict(
    device_id: int = Query(...),
    weekday: int = Query(...),
    start_time: str = Query(...),  # "HH:MM"
    end_time: str = Query(...),    # "HH:MM"
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    st = time.fromisoformat(start_time)
    et = time.fromisoformat(end_time)
    conflict = db.query(ScheduleEntry).filter(
        ScheduleEntry.device_id == device_id,
        ScheduleEntry.weekday == weekday,
        ScheduleEntry.start_time < et,
        ScheduleEntry.end_time > st,
    ).first()
    if conflict:
        return {"conflict": True, "message": f"Zeitkonflikt: Geraet ist bereits belegt am {weekday_name(conflict.weekday)} {conflict.start_time.strftime('%H:%M')}-{conflict.end_time.strftime('%H:%M')} (Klasse {conflict.class_name})."}
    return {"conflict": False}
```

### Pico CSS Nav Bar (verified pattern)
```html
<!-- Source: https://picocss.com/docs/nav -->
<nav>
  <ul>
    <li><strong>SmartAttend</strong></li>
  </ul>
  <ul>
    <li><a href="/admin/devices">Geraete</a></li>
    <li><a href="/admin/users">Benutzer</a></li>
    <li>
      <form method="post" action="/auth/logout" style="margin: 0;">
        <button type="submit" class="outline secondary">Abmelden</button>
      </form>
    </li>
  </ul>
</nav>
```

### Inline Edit Change Detection (vanilla JS)
```javascript
// Source: Discretion area -- recommended minimal implementation
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('edit-form');
  if (!form) return;
  const inputs = form.querySelectorAll('input[data-original], select[data-original]');
  const saveBtn = document.getElementById('save-btn');
  const resetBtn = document.getElementById('reset-btn');

  function hasChanges() {
    return Array.from(inputs).some(el => el.value !== el.dataset.original);
  }

  function updateButtons() {
    const changed = hasChanges();
    saveBtn.disabled = !changed;
    resetBtn.disabled = !changed;
  }

  inputs.forEach(el => el.addEventListener('input', updateButtons));

  resetBtn?.addEventListener('click', () => {
    inputs.forEach(el => { el.value = el.dataset.original; });
    updateButtons();
  });
});
```

### Datalist for Class Dropdown with Auto-Create
```html
<!-- Source: Discretion area -- HTML5 datalist allows typing + autocomplete -->
<label for="class_name">Klasse</label>
<input type="text" id="class_name" name="class_name" list="class-options" placeholder="z.B. 10A">
<datalist id="class-options">
  {% for cls in school_classes %}
  <option value="{{ cls.name }}">
  {% endfor %}
</datalist>
<!-- Server-side: if submitted class_name not in SchoolClass table, auto-create it -->
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Jinja2Templates(directory=...) no `request` | `request` required as first TemplateResponse param | FastAPI 0.95+ / Starlette 0.29+ | Must pass `request=request` (already done in Phase 2) |
| Pico CSS v1 `--del-color` | Pico CSS v2 `--pico-del-color` prefix | Pico v2.0 (2023) | Must use `--pico-` prefix in new templates |
| Flask-style flash() messages | FastAPI has no built-in flash | Always | Use query params or session middleware |

## Open Questions

1. **SchoolClass FK strategy: integer FK vs string FK?**
   - What we know: D-13 says "class_name becomes FK reference to SchoolClass". This could mean storing `school_class_id` (int FK) or keeping `class_name` as a string FK to `SchoolClass.name`.
   - What's unclear: Whether to add a new integer column or keep the string column with a FK constraint.
   - Recommendation: Use integer FK (`school_class_id` -> `SchoolClass.id`) for cleaner normalization. Keep `class_name` as a convenience property or drop it. The integer approach avoids cascading renames if a class name changes. However, since SQLite + create_all (no Alembic), modifying existing columns is hard. Simpler alternative: keep `class_name` as a plain string and validate against SchoolClass table in application code (no DB-level FK). This avoids migration complexity for a prototype.

2. **`<details>` + device table layout**
   - What we know: D-07 says expandable rows via `<details>`. But `<details>` inside `<table>` is invalid HTML.
   - Recommendation: Use a `<details>` per device (outside any table), where the `<summary>` shows the device row info in a grid layout, and the expanded content shows the schedule table + add form. This is semantically correct and Pico CSS styles `<details>` natively.

3. **`/admin` redirect target**
   - What we know: Auth router redirects admin to `/admin` (line 74 of auth.py). Phase 3 needs to handle this.
   - Recommendation: Add a GET `/admin` route that redirects to `/admin/devices` (the primary admin page).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 |
| Config file | none (uses default discovery) |
| Quick run command | `pytest tests/test_admin.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ADMIN-01 | GET /admin/devices shows device table with status | integration | `pytest tests/test_admin.py::test_devices_page_shows_devices -x` | Wave 0 |
| ADMIN-02 | POST /admin/devices/update changes room/label | integration | `pytest tests/test_admin.py::test_update_device_room_label -x` | Wave 0 |
| ADMIN-03 | POST /admin/devices/{id}/toggle flips is_enabled | integration | `pytest tests/test_admin.py::test_toggle_device_enabled -x` | Wave 0 |
| ADMIN-04 | GET /admin/users shows user table | integration | `pytest tests/test_admin.py::test_users_page_shows_users -x` | Wave 0 |
| ADMIN-05 | POST /admin/users/create creates user | integration | `pytest tests/test_admin.py::test_create_user -x` | Wave 0 |
| ADMIN-06 | POST /admin/users/{id}/deactivate sets is_active=False | integration | `pytest tests/test_admin.py::test_deactivate_user -x` | Wave 0 |
| ADMIN-07 | Schedule entries visible in device details | integration | `pytest tests/test_admin.py::test_device_schedule_entries_shown -x` | Wave 0 |
| ADMIN-08 | POST /admin/schedule/add creates entry | integration | `pytest tests/test_admin.py::test_add_schedule_entry -x` | Wave 0 |
| ADMIN-09 | Overlapping schedule entry rejected | integration | `pytest tests/test_admin.py::test_schedule_conflict_rejected -x` | Wave 0 |
| ADMIN-10 | POST /admin/schedule/{id}/delete removes entry | integration | `pytest tests/test_admin.py::test_delete_schedule_entry -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_admin.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_admin.py` -- all 10 ADMIN requirement tests (new file)
- [ ] Helper fixture in `tests/conftest.py` for creating admin-authenticated test_client (login + cookie)
- [ ] Helper fixture for seeding test devices and schedule entries

## Sources

### Primary (HIGH confidence)
- Project codebase: `app/routers/auth.py`, `app/dependencies.py`, `app/models/*.py` -- established patterns
- Pico CSS v2.1.1 docs (https://picocss.com/docs/nav) -- nav structure
- `app/static/pico.min.css` header confirms v2.1.1

### Secondary (MEDIUM confidence)
- FastAPI flash message discussion (https://github.com/fastapi/fastapi/discussions/6088) -- confirmed no built-in flash, query param approach viable
- Pico CSS examples repo (https://github.com/picocss/examples) -- confirmed nav ul/ul pattern

### Tertiary (LOW confidence)
- None -- all findings verified against codebase or official docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all packages already installed and proven in Phases 1-2
- Architecture: HIGH -- follows established router/template/model patterns from Phase 2
- Pitfalls: HIGH -- derived from codebase inspection (HTML nesting, session commits, CSS var names)
- JS patterns: MEDIUM -- vanilla JS approach is straightforward but untested in this project (first JS file)

**Research date:** 2026-03-29
**Valid until:** 2026-04-28 (stable stack, no fast-moving dependencies)
