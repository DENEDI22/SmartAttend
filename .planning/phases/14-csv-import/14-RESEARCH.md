# Phase 14: CSV Import - Research

**Researched:** 2026-04-08
**Domain:** CSV file upload, parsing, validation preview, bulk database operations
**Confidence:** HIGH

## Summary

This phase adds CSV bulk import for users and schedule entries. The existing codebase already uses Python's `csv` module for export (teacher.py), FastAPI `Form()` for data submission, and has all validation logic in admin.py (email uniqueness, role validation, schedule conflict detection). The main new element is `UploadFile` for file handling and a two-step POST flow (upload -> preview -> confirm).

No new dependencies are needed. Python stdlib `csv` and `io` modules handle parsing. FastAPI's `UploadFile` (backed by `python-multipart`, already installed v0.0.22) handles file upload. The all-or-nothing validation model (D-06) simplifies the confirm step -- just re-parse and commit if zero errors.

**Primary recommendation:** Build two parallel flows (user CSV, schedule CSV) each with 3 endpoints: template download GET, upload POST returning preview, confirm POST committing data. Store parsed+validated data in a hidden form field (JSON) on the preview page to avoid re-uploading on confirm.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-01: Comma-delimited CSV (standard comma separator, not semicolons)
- D-02: User CSV template columns: `email, first_name, last_name, role, class_name, password` -- password is plaintext in CSV, server hashes on import
- D-03: Schedule CSV references teachers by email and devices by device_id string (e.g. "e101") -- human-readable, resolved to FK IDs on import
- D-04: Template download provides pre-filled header row with example data row (commented or as placeholder)
- D-05: Validation preview shows all rows in a Pico CSS table with red highlighting on invalid rows; error message in a last column per row
- D-06: All-or-nothing import -- if any row has errors, nothing is committed. Admin must fix all errors and re-upload
- D-07: Schedule CSV validates for device+weekday+time overlaps (same logic as existing manual schedule form conflict check)
- D-08: CSV import sections embedded on existing admin pages -- user import on /admin/users, schedule import on /admin/devices
- D-09: Two-step flow: Step 1 = file upload form, Step 2 = server parses and shows validation table with confirm/back buttons. Single page with form replacement (POST returns preview, second POST confirms)
- D-10: Duplicate emails trigger upsert -- if email exists, update that user's fields with CSV values
- D-11: Schedule overlap detection flags overlapping entries as errors (reuse existing conflict check logic)

### Claude's Discretion
- D-12: Max CSV file size -- use 1 MB (sufficient for thousands of rows, prevents abuse)
- D-13: CSV encoding handling -- detect UTF-8 BOM, fall back to latin-1 for German Excel exports
- D-14: Template download format details -- header row + one commented example row

### Deferred Ideas (OUT OF SCOPE)
None.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CSV-01 | Admin can download a template CSV for user import | Template download endpoint returning `StreamingResponse` with CSV content |
| CSV-02 | Admin can upload a user CSV and see validation preview with per-row errors | `UploadFile` + `csv.DictReader` + validation logic from existing `users_create` |
| CSV-03 | Admin can confirm user CSV import (only valid rows committed) | All-or-nothing: re-validate, then bulk insert/upsert in single transaction |
| CSV-04 | Admin can download a template CSV for schedule import | Same pattern as CSV-01, different columns |
| CSV-05 | Admin can upload schedule CSV with overlap/FK error preview | Device lookup by `device_id` string, teacher lookup by email, `check_schedule_conflict` reuse |
| CSV-06 | Admin can confirm schedule CSV import (only valid rows committed) | Same all-or-nothing pattern as CSV-03 |

</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Tech Stack: FastAPI + Jinja2 + SQLAlchemy + SQLite + Pico CSS
- CSS: Pico CSS, served locally -- no CDN, no JS builds
- Database: SQLite
- Zero new dependencies (v1.2 decision from STATE.md)

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| csv (stdlib) | N/A | CSV parsing/writing | Already used in teacher.py export |
| io (stdlib) | N/A | StringIO for CSV generation | Already used in teacher.py export |
| FastAPI UploadFile | 0.135.3 | File upload handling | Built into FastAPI, python-multipart already installed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-multipart | 0.0.22 | UploadFile backend | Already installed, required by UploadFile |

No new packages to install.

## Architecture Patterns

### Endpoint Structure

Each CSV flow (user, schedule) needs 3 endpoints:

```
GET  /admin/users/csv-template      -> download user CSV template
POST /admin/users/csv-upload         -> parse, validate, return preview page
POST /admin/users/csv-confirm        -> re-validate, commit to DB

GET  /admin/schedule/csv-template    -> download schedule CSV template
POST /admin/schedule/csv-upload      -> parse, validate, return preview page
POST /admin/schedule/csv-confirm     -> re-validate, commit to DB
```

### Pattern: Upload -> Preview -> Confirm

**Step 1 (upload):** Accept `UploadFile`, read bytes, decode (UTF-8 with BOM detection, fallback latin-1), parse with `csv.DictReader`, validate each row, render preview template.

**Step 2 (confirm):** Receive validated data as JSON in a hidden form field. Re-parse and re-validate server-side (never trust client data), then commit in a single transaction.

```python
from fastapi import UploadFile, File

@router.post("/users/csv-upload")
async def users_csv_upload(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    # Read and decode
    contents = await file.read()
    if len(contents) > 1_048_576:  # 1 MB limit
        return RedirectResponse(url="/admin/users?error=Datei+zu+gross.", status_code=303)
    
    # Decode with BOM detection
    text = contents.decode("utf-8-sig") if contents[:3] == b'\xef\xbb\xbf' else None
    if text is None:
        try:
            text = contents.decode("utf-8")
        except UnicodeDecodeError:
            text = contents.decode("latin-1")
    
    # Parse CSV
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for i, row in enumerate(reader, start=2):
        errors = validate_user_row(row, db)
        rows.append({**row, "row_num": i, "errors": errors})
    
    has_errors = any(r["errors"] for r in rows)
    
    # Render preview with rows data
    return templates.TemplateResponse("admin_users_csv_preview.html", {
        "request": request, "user": user, "rows": rows,
        "has_errors": has_errors,
        "rows_json": json.dumps([...]),  # hidden field data
    })
```

### Pattern: Template Download

```python
@router.get("/users/csv-template")
async def users_csv_template(user: User = Depends(require_role("admin"))):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["email", "first_name", "last_name", "role", "class_name", "password"])
    writer.writerow(["max.mustermann@schule.de", "Max", "Mustermann", "student", "10A", "passwort123"])
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="benutzer_vorlage.csv"'},
    )
```

### Schedule CSV Template Columns

Based on D-03 and ScheduleEntry model:
```
device_id, teacher_email, class_name, weekday, start_time, end_time, late_threshold_minutes
```

Where:
- `device_id` = string like "e101" (resolved via `Device.device_id`)
- `teacher_email` = email string (resolved via `User.email` where role=teacher)
- `weekday` = 0-6 (Monday-Sunday)
- `start_time` / `end_time` = "HH:MM" format
- `late_threshold_minutes` = optional integer, empty = use global default

### Validation Functions

**User row validation:**
1. Required fields present and non-empty: email, first_name, last_name, role, password
2. Valid email format (basic check)
3. Role in ("admin", "teacher", "student")
4. Password minimum length (reuse existing rules if any)
5. For upsert (D-10): existing email is not an error, just flags as update

**Schedule row validation:**
1. Required fields: device_id, teacher_email, class_name, weekday, start_time, end_time
2. Device exists (lookup by device_id string)
3. Teacher exists (lookup by email, role=teacher)
4. Weekday is 0-6
5. Time format valid, start < end
6. No overlap with existing schedule entries (reuse `check_schedule_conflict`)
7. No overlap between rows within the CSV itself

### Preview Template Pattern

```html
<table>
  <thead>
    <tr><th>#</th><th>Email</th>...<th>Status</th></tr>
  </thead>
  <tbody>
    {% for row in rows %}
    <tr {% if row.errors %}style="background: var(--pico-del-color, #e53935); color: white;"{% endif %}>
      <td>{{ row.row_num }}</td>
      <td>{{ row.email }}</td>
      ...
      <td>{% if row.errors %}{{ row.errors | join('; ') }}{% else %}OK{% endif %}</td>
    </tr>
    {% endfor %}
  </tbody>
</table>
```

### Anti-Patterns to Avoid
- **Storing uploaded file on disk:** Not needed. Read into memory, parse, done. 1 MB limit ensures safety.
- **Client-side validation:** No JS builds constraint. All validation server-side.
- **Separate preview page URL:** D-09 says same page with form replacement. POST returns the preview directly.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CSV parsing | Manual string splitting | `csv.DictReader` | Handles quoting, escaping, edge cases |
| Encoding detection | Custom BOM parsing | `utf-8-sig` codec | Python stdlib handles BOM transparently |
| Password hashing | Custom hash | `get_password_hash()` from auth.py | Already exists, uses passlib+bcrypt |
| Schedule conflict check | New overlap logic | `check_schedule_conflict()` from admin.py | Already tested and correct |

## Common Pitfalls

### Pitfall 1: Encoding Issues with German Excel
**What goes wrong:** German Excel exports CSV as Windows-1252/latin-1, not UTF-8. Characters like umlauts break.
**How to avoid:** Try UTF-8 first (with BOM detection via `utf-8-sig`), fall back to `latin-1` on `UnicodeDecodeError`.

### Pitfall 2: CSV Intra-file Overlap Detection
**What goes wrong:** `check_schedule_conflict` only checks existing DB entries. Two rows in the same CSV could overlap with each other.
**How to avoid:** After DB conflict check, also check each schedule row against all previously validated rows in the same upload.

### Pitfall 3: Empty Rows / Trailing Newlines
**What goes wrong:** CSV files often have trailing empty lines. `csv.DictReader` may produce rows with all-empty values.
**How to avoid:** Skip rows where all values are empty or whitespace-only.

### Pitfall 4: Confirm Step Data Integrity
**What goes wrong:** Data in hidden form field could be tampered with between preview and confirm.
**How to avoid:** Re-validate everything on confirm POST. Never trust the preview data blindly.

### Pitfall 5: SchoolClass Auto-Creation
**What goes wrong:** New class names in CSV not in SchoolClass table cause issues.
**How to avoid:** Reuse existing auto-create pattern from `users_create` and `schedule_add` -- flush after creating new SchoolClass entries.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | pyproject.toml (assumed) or pytest defaults |
| Quick run command | `pytest tests/test_admin.py -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CSV-01 | User template download returns valid CSV | unit | `pytest tests/test_csv_import.py::test_user_template_download -x` | Wave 0 |
| CSV-02 | User CSV upload shows validation preview | unit | `pytest tests/test_csv_import.py::test_user_csv_preview -x` | Wave 0 |
| CSV-03 | User CSV confirm commits valid rows | unit | `pytest tests/test_csv_import.py::test_user_csv_confirm -x` | Wave 0 |
| CSV-04 | Schedule template download returns valid CSV | unit | `pytest tests/test_csv_import.py::test_schedule_template_download -x` | Wave 0 |
| CSV-05 | Schedule CSV upload shows validation preview | unit | `pytest tests/test_csv_import.py::test_schedule_csv_preview -x` | Wave 0 |
| CSV-06 | Schedule CSV confirm commits valid rows | unit | `pytest tests/test_csv_import.py::test_schedule_csv_confirm -x` | Wave 0 |

### Additional Test Cases
- User CSV with duplicate email -> upsert behavior verified
- User CSV with invalid role -> error shown in preview
- Schedule CSV with nonexistent device -> error shown
- Schedule CSV with intra-file overlap -> error shown
- Empty CSV (header only) -> appropriate message
- Encoding: latin-1 file with umlauts parsed correctly
- File over 1 MB rejected

### Sampling Rate
- **Per task commit:** `pytest tests/test_csv_import.py -x -q`
- **Per wave merge:** `pytest tests/ -x -q`
- **Phase gate:** Full suite green

### Wave 0 Gaps
- [ ] `tests/test_csv_import.py` -- all CSV import tests (new file)
- [ ] Test helper: function to create in-memory CSV `UploadFile` for testing

## Code Examples

### Creating UploadFile for Tests

```python
import io
from fastapi import UploadFile

def make_csv_upload(content: str, filename: str = "test.csv") -> dict:
    """Create upload file data for TestClient."""
    return {"file": (filename, io.BytesIO(content.encode("utf-8")), "text/csv")}

# Usage in test:
csv_content = "email,first_name,last_name,role,class_name,password\ntest@school.de,Max,Muster,student,10A,pass123"
response = admin_client.post("/admin/users/csv-upload", files=make_csv_upload(csv_content))
```

### Confirm Flow with Hidden JSON

```python
import json

@router.post("/users/csv-confirm")
async def users_csv_confirm(
    request: Request,
    rows_json: str = Form(...),
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    rows = json.loads(rows_json)
    # Re-validate all rows
    errors = []
    for row in rows:
        row_errors = validate_user_row(row, db)
        if row_errors:
            errors.extend(row_errors)
    
    if errors:
        return RedirectResponse(url="/admin/users?error=Validierungsfehler.", status_code=303)
    
    # Commit all rows in single transaction
    for row in rows:
        existing = db.query(User).filter(User.email == row["email"]).first()
        if existing:  # Upsert (D-10)
            existing.first_name = row["first_name"]
            existing.last_name = row["last_name"]
            existing.role = row["role"]
            existing.class_name = row.get("class_name") or None
            existing.password_hash = get_password_hash(row["password"])
        else:
            # Auto-create SchoolClass if needed
            # ... create new User
            pass
    
    db.commit()
    return RedirectResponse(url=f"/admin/users?msg={len(rows)}+Benutzer+importiert.", status_code=303)
```

## Open Questions

1. **Schedule CSV template: include `late_threshold_minutes`?**
   - ScheduleEntry model has this field
   - Recommendation: Include as optional column. Empty = NULL (global default). Keeps parity with manual form.

2. **Preview page: new template or inline in existing?**
   - D-08 says embedded on existing pages, D-09 says form replacement
   - Recommendation: Create separate `admin_users_csv_preview.html` and `admin_schedule_csv_preview.html` that extend `admin_base.html`. The upload POST renders these instead of redirecting. Simpler than trying to conditionally show/hide sections in existing templates.

## Sources

### Primary (HIGH confidence)
- Existing codebase: `app/routers/admin.py` -- user creation, schedule creation, conflict check logic
- Existing codebase: `app/routers/teacher.py` lines 278-320 -- CSV export pattern with `csv` module
- Existing codebase: `app/models/user.py`, `app/models/schedule_entry.py`, `app/models/device.py` -- model fields
- FastAPI 0.135.3 -- UploadFile documentation (training data, HIGH confidence for stable API)

### Secondary (MEDIUM confidence)
- python-multipart 0.0.22 installed -- confirmed via pip

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all stdlib + existing dependencies, zero new packages
- Architecture: HIGH - follows established patterns in codebase exactly
- Pitfalls: HIGH - common CSV handling issues well-documented

**Research date:** 2026-04-08
**Valid until:** 2026-05-08 (stable domain, no fast-moving dependencies)
