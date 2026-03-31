# Phase 4: Teacher Interface - Research

**Researched:** 2026-03-29
**Domain:** FastAPI + Jinja2 server-rendered teacher dashboard, attendance roster, CSV export
**Confidence:** HIGH

## Summary

Phase 4 builds a read-only teacher interface with three routes: a dashboard showing today's lessons (`/teacher`), a lesson attendance detail view (`/teacher/lesson/<token_id>`), and a CSV export endpoint (`/teacher/lesson/<token_id>/csv`). The implementation closely mirrors the admin router pattern established in Phase 3 -- same Jinja2Templates setup, same `require_role()` dependency, same flash message pattern, same two-level template inheritance.

The data model is fully in place from Phases 1 and 3. The key query pattern is: ScheduleEntry (filtered by teacher_id + weekday) joined to AttendanceToken (filtered by lesson_date = today) joined to AttendanceRecord (counted per token). The full class roster requires querying all active students with matching `class_name`, then left-joining against AttendanceRecord to determine presence/absence.

**Primary recommendation:** Follow the admin router pattern exactly. No new dependencies needed. The CSV export uses Python's built-in `csv` and `io` modules with FastAPI's `StreamingResponse` or plain `Response`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Table view for today's lessons at `/teacher`. Columns: Klasse, Raum, Zeit, Anwesend (X/Y), Details-Link. Table rows are read-only.
- **D-02:** Expected student count = `SELECT COUNT(*) FROM users WHERE role='student' AND class_name = schedule_entry.class_name AND is_active = True`.
- **D-03:** Checked-in count = number of AttendanceRecords linked to the AttendanceToken for that schedule_entry + today's date.
- **D-04:** Only show lessons for today (current weekday) where teacher_id matches logged-in teacher.
- **D-05:** Full class roster at `/teacher/lesson/<token_id>`. Shows ALL students in the class, not just checked in. Columns: Name (Nachname, Vorname), Status, Uhrzeit.
- **D-06:** Header shows: class name, room, time range, and "Anwesend: X/Y" summary.
- **D-07:** "CSV herunterladen" link below the table to download attendance as CSV.
- **D-08:** Full roster with status. CSV columns: Nachname;Vorname;Klasse;Status;Uhrzeit. Semicolon separator.
- **D-09:** UTF-8 encoding with BOM for Excel compatibility.
- **D-10:** Filename format: `Anwesenheit_{Klasse}_{YYYY-MM-DD}.csv`.
- **D-11:** Absent students have empty Uhrzeit field.
- **D-12:** Separate `teacher_base.html` extending `base.html`. Nav: SmartAttend brand, Uebersicht link, Abmelden button.
- **D-13:** Teacher router at `app/routers/teacher.py` with prefix `/teacher`. All routes protected by `require_role("teacher")`.
- **D-14:** Flash messages via query params (same `?msg=` / `?error=` pattern as admin).

### Claude's Discretion
- Empty state when teacher has no lessons today ("Heute keine Stunden geplant")
- Sorting order of attendance list (alphabetical by last name)
- How to handle the case where AttendanceToken doesn't exist yet (lesson hasn't started, scheduler hasn't issued token)
- Template file naming (teacher_dashboard.html, teacher_lesson.html, etc.)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TEACH-01 | Teacher can view today's lessons on their dashboard | D-01, D-04: ScheduleEntry filtered by teacher_id + weekday, rendered as table at `/teacher` |
| TEACH-02 | Each lesson shows checked-in count vs expected student count | D-02, D-03: Expected = active students with matching class_name; Checked-in = AttendanceRecords for that token |
| TEACH-03 | Teacher can view full attendance list for a specific lesson | D-05, D-06: Full class roster at `/teacher/lesson/<token_id>` with present/absent status |
| TEACH-04 | Teacher can export attendance as CSV | D-07 through D-11: Semicolon-separated, UTF-8 BOM, filename format, full roster |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Tech Stack**: FastAPI + Jinja2 + SQLAlchemy + SQLite + Pico CSS (all already in place)
- **CSS**: Pico CSS served locally from `static/` -- no CDN, no JS builds
- **Database**: SQLite (zero config)
- **No JS required** for teacher pages (read-only, no inline editing)
- **GSD Workflow**: All edits through GSD commands

## Standard Stack

### Core (already installed)
| Library | Purpose | Why Standard |
|---------|---------|--------------|
| FastAPI | Web framework, router, dependencies | Already used in auth + admin phases |
| Jinja2 (via FastAPI) | Server-rendered HTML templates | Established pattern |
| SQLAlchemy | ORM queries for schedule, attendance, users | Already used throughout |
| Pico CSS | Classless CSS styling | Project constraint |

### Supporting (Python stdlib -- no install needed)
| Library | Purpose | When to Use |
|---------|---------|-------------|
| `csv` (stdlib) | CSV generation | CSV export endpoint |
| `io.StringIO` (stdlib) | In-memory string buffer | CSV writing to buffer |
| `datetime` (stdlib) | Date/weekday calculations | Dashboard filtering |

**Installation:** No new packages needed. Everything is already in `requirements.txt`.

## Architecture Patterns

### New Files
```
app/
  routers/
    teacher.py           # New: teacher router (3 GET endpoints + 1 CSV)
  templates/
    teacher_base.html    # New: extends base.html (nav, flash messages)
    teacher_dashboard.html  # New: today's lessons table
    teacher_lesson.html  # New: attendance roster + CSV link
```

### Pattern 1: Router Setup (mirror admin.py)
**What:** Create `app/routers/teacher.py` with `APIRouter(prefix="/teacher")`, register in `main.py`.
**When to use:** Every route in this phase.
**Example:**
```python
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/teacher", tags=["teacher"])

WEEKDAY_NAMES = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
```

### Pattern 2: Dashboard Query (TEACH-01, TEACH-02)
**What:** Query today's lessons for the logged-in teacher, enriched with attendance counts.
**Key logic:**
```python
from datetime import date, datetime

today = date.today()
weekday = today.weekday()  # 0=Monday matches ScheduleEntry.weekday

# Get teacher's lessons for today
lessons = db.query(ScheduleEntry).filter(
    ScheduleEntry.teacher_id == user.id,
    ScheduleEntry.weekday == weekday,
).order_by(ScheduleEntry.start_time).all()

# For each lesson, find token and counts
for lesson in lessons:
    token = db.query(AttendanceToken).filter(
        AttendanceToken.schedule_entry_id == lesson.id,
        AttendanceToken.lesson_date == today,
    ).first()

    expected = db.query(User).filter(
        User.role == "student",
        User.class_name == lesson.class_name,
        User.is_active == True,
    ).count()

    checked_in = 0
    if token:
        checked_in = db.query(AttendanceRecord).filter(
            AttendanceRecord.token_id == token.id,
        ).count()
```

### Pattern 3: Full Class Roster (TEACH-03)
**What:** Show ALL students in the class with present/absent status.
**Key logic:**
```python
# All active students in the class, sorted by last_name then first_name
students = db.query(User).filter(
    User.role == "student",
    User.class_name == schedule_entry.class_name,
    User.is_active == True,
).order_by(User.last_name, User.first_name).all()

# Get check-in records for this token
records = {r.student_id: r for r in db.query(AttendanceRecord).filter(
    AttendanceRecord.token_id == token.id,
).all()}

# Build roster
roster = []
for student in students:
    record = records.get(student.id)
    roster.append({
        "last_name": student.last_name,
        "first_name": student.first_name,
        "status": "Anwesend" if record else "Abwesend",
        "time": record.checked_in_at.strftime("%H:%M") if record else "",
    })
```

### Pattern 4: CSV Export (TEACH-04)
**What:** Return a CSV file as a download response.
**Key logic:**
```python
import csv
import io

@router.get("/lesson/{token_id}/csv")
async def lesson_csv(token_id: int, user: User = Depends(require_role("teacher")), db: Session = Depends(get_db)):
    # ... query roster same as Pattern 3 ...

    output = io.StringIO()
    output.write("\ufeff")  # UTF-8 BOM for Excel
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Nachname", "Vorname", "Klasse", "Status", "Uhrzeit"])
    for row in roster:
        writer.writerow([row["last_name"], row["first_name"], class_name, row["status"], row["time"]])

    filename = f"Anwesenheit_{class_name}_{today.strftime('%Y-%m-%d')}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
```

### Pattern 5: Template Inheritance
**What:** Two-level template hierarchy matching admin pattern.
```
base.html
  -> teacher_base.html (nav + flash messages + {% block teacher_content %})
    -> teacher_dashboard.html
    -> teacher_lesson.html
```

### Pattern 6: Access Control on Lesson Detail
**What:** Verify the lesson belongs to the logged-in teacher.
```python
token = db.query(AttendanceToken).filter(AttendanceToken.id == token_id).first()
if not token:
    return RedirectResponse(url="/teacher?error=Stunde+nicht+gefunden.", status_code=303)

schedule_entry = db.query(ScheduleEntry).filter(ScheduleEntry.id == token.schedule_entry_id).first()
if schedule_entry.teacher_id != user.id:
    return RedirectResponse(url="/teacher?error=Sie+haben+keinen+Zugriff+auf+diese+Stunde.", status_code=303)
```

### Anti-Patterns to Avoid
- **Querying inside Jinja2 templates:** All data should be fetched in the route handler and passed as context. Never pass `db` to templates.
- **Using `csv.DictWriter` without controlling field order:** Use `csv.writer` with explicit row lists to ensure column order matches the spec.
- **Forgetting UTF-8 BOM:** Excel on Windows will not interpret UTF-8 correctly without the BOM prefix `\ufeff`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CSV generation | String concatenation with `;` | Python `csv.writer(delimiter=";")` | Handles quoting, escaping special characters in names (e.g., semicolons in names) |
| Date/weekday logic | Manual weekday mapping | `datetime.date.today().weekday()` | Already matches ScheduleEntry.weekday (0=Monday) |
| Access control | Manual JWT parsing in teacher routes | `require_role("teacher")` dependency | Already tested and working from Phase 2 |

## Important Design Note: "Fach" Column

The UI spec lists "Fach" (subject) as a dashboard table column header. However, per Phase 1 decision D-07, **ScheduleEntry has NO subject field**. The planner must reconcile this:
- **Recommendation:** Drop the "Fach" column from the dashboard table. The remaining columns (Klasse, Raum, Zeit, Anwesend, Details-Link) fully identify each lesson. The CONTEXT.md D-01 decision lists exactly these columns without "Fach", which is the authoritative source.
- The UI-SPEC was generated after the discussion and may have added "Fach" speculatively. D-01 in CONTEXT.md is the locked decision.

## Common Pitfalls

### Pitfall 1: Token Not Yet Issued
**What goes wrong:** Dashboard crashes or shows wrong data when no AttendanceToken exists for a scheduled lesson (scheduler hasn't run yet).
**Why it happens:** Phase 6 (MQTT/Scheduler) creates tokens. In Phase 4, tokens may not exist for today's lessons.
**How to avoid:** Check if token is None. If so, show `--` in the Anwesend column and omit the Details link. This is already covered in CONTEXT.md discretion areas and UI-SPEC.
**Warning signs:** NoneType errors when accessing `token.id`.

### Pitfall 2: Room Name from Device, Not ScheduleEntry
**What goes wrong:** ScheduleEntry has no `room` field. Room is stored on the Device model.
**Why it happens:** The data model separates device assignment (room) from schedule (class, time, teacher).
**How to avoid:** Join through Device: `ScheduleEntry.device_id -> Device.id -> Device.room`. Query the Device for each lesson's room.
**Warning signs:** Missing "Raum" column data in dashboard.

### Pitfall 3: SQLite In-Memory Test Isolation
**What goes wrong:** Tests fail with stale data or missing records after commits.
**Why it happens:** SQLAlchemy sessions on in-memory SQLite need `StaticPool` and `db_session.refresh()` after commits.
**How to avoid:** Use established `conftest.py` patterns. Always `db_session.refresh(obj)` after `db_session.commit()`.
**Warning signs:** Objects have None IDs or stale field values in assertions.

### Pitfall 4: CSV Encoding for German Characters
**What goes wrong:** Umlauts display as garbage in Excel.
**Why it happens:** Excel defaults to system locale encoding, not UTF-8.
**How to avoid:** Prepend UTF-8 BOM (`\ufeff`) to the CSV content. Use `text/csv; charset=utf-8` content type.
**Warning signs:** Characters like ae, oe, ue show as multi-byte sequences.

### Pitfall 5: Teacher Client Fixture Missing
**What goes wrong:** No `teacher_client` fixture exists in conftest.py yet (only `admin_client`).
**Why it happens:** Phase 2/3 only needed admin-authenticated test clients.
**How to avoid:** Create a `teacher_client` fixture in conftest.py following the same pattern as `admin_client`.
**Warning signs:** Tests cannot authenticate as teacher.

## Code Examples

### Teacher Client Test Fixture
```python
@pytest.fixture
def teacher_client(test_client, db_session, seed_teacher):
    """TestClient pre-authenticated as teacher."""
    resp = test_client.post(
        "/auth/login",
        data={"email": "teacher@test.com", "password": "teacherpass", "next": ""},
    )
    assert resp.status_code == 303
    return test_client
```

### Registering Router in main.py
```python
from app.routers.teacher import router as teacher_router  # noqa: E402
app.include_router(teacher_router)
```

### Template: teacher_base.html
```html
{% extends "base.html" %}
{% block content %}
<nav>
  <ul>
    <li><strong>SmartAttend</strong></li>
  </ul>
  <ul>
    <li><a href="/teacher" {% if active_page == 'overview' %}aria-current="page"{% endif %}>Uebersicht</a></li>
    <li>
      <form method="post" action="/auth/logout" style="margin: 0;">
        <button type="submit" class="outline secondary" style="margin: 0; padding: 0.5rem 1rem;">Abmelden</button>
      </form>
    </li>
  </ul>
</nav>
{% if request.query_params.get('msg') %}
<p role="alert" style="color: #2e7d32">{{ request.query_params.get('msg') }}</p>
{% endif %}
{% if request.query_params.get('error') %}
<p role="alert" style="color: var(--pico-del-color)">{{ request.query_params.get('error') }}</p>
{% endif %}
{% block teacher_content %}{% endblock %}
{% endblock %}
```

### FastAPI Response for CSV
```python
from fastapi.responses import Response

return Response(
    content=csv_string,
    media_type="text/csv; charset=utf-8",
    headers={"Content-Disposition": f'attachment; filename="{filename}"'},
)
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already configured) |
| Config file | `tests/conftest.py` (exists) |
| Quick run command | `python -m pytest tests/test_teacher.py -x -q` |
| Full suite command | `python -m pytest tests/ -x -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TEACH-01 | Teacher dashboard shows today's lessons | integration | `python -m pytest tests/test_teacher.py::test_dashboard_shows_todays_lessons -x` | Wave 0 |
| TEACH-01 | Dashboard empty state when no lessons | integration | `python -m pytest tests/test_teacher.py::test_dashboard_empty_state -x` | Wave 0 |
| TEACH-02 | Attendance count X/Y displayed | integration | `python -m pytest tests/test_teacher.py::test_dashboard_shows_attendance_count -x` | Wave 0 |
| TEACH-02 | Dashboard shows -- when no token yet | integration | `python -m pytest tests/test_teacher.py::test_dashboard_no_token_shows_dash -x` | Wave 0 |
| TEACH-03 | Full roster with present/absent status | integration | `python -m pytest tests/test_teacher.py::test_lesson_roster_full_class -x` | Wave 0 |
| TEACH-03 | Access denied for other teacher's lesson | integration | `python -m pytest tests/test_teacher.py::test_lesson_access_denied_other_teacher -x` | Wave 0 |
| TEACH-04 | CSV download with correct content | integration | `python -m pytest tests/test_teacher.py::test_csv_export_content -x` | Wave 0 |
| TEACH-04 | CSV has UTF-8 BOM and semicolons | integration | `python -m pytest tests/test_teacher.py::test_csv_encoding_and_format -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_teacher.py -x -q`
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_teacher.py` -- covers TEACH-01 through TEACH-04
- [ ] `teacher_client` fixture in `tests/conftest.py` -- pre-authenticated teacher test client
- [ ] Seed fixtures for: ScheduleEntry + AttendanceToken + AttendanceRecord + multiple students

## Sources

### Primary (HIGH confidence)
- Existing codebase: `app/routers/admin.py`, `app/dependencies.py`, `app/models/*.py` -- direct code inspection
- `04-CONTEXT.md` -- locked decisions from user discussion
- `04-UI-SPEC.md` -- UI design contract
- `tests/conftest.py`, `tests/test_admin.py` -- established test patterns

### Secondary (MEDIUM confidence)
- Python `csv` module documentation -- stdlib, stable API
- FastAPI `Response` class -- well-established pattern for custom responses

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in use, no new dependencies
- Architecture: HIGH -- direct mirror of admin router pattern from Phase 3
- Pitfalls: HIGH -- identified from direct codebase inspection and data model analysis

**Research date:** 2026-03-29
**Valid until:** 2026-04-28 (stable -- no moving parts, all internal codebase)
