# Phase 5: Student Check-in - Research

**Researched:** 2026-03-29
**Domain:** FastAPI check-in endpoint + Jinja2 template + SQLAlchemy token validation
**Confidence:** HIGH

## Summary

Phase 5 implements the student-facing check-in flow: a student taps an NFC device, opens a URL with a token UUID, authenticates (or uses existing session), and confirms attendance. The codebase already has all required models (AttendanceToken, AttendanceRecord, ScheduleEntry, Device), authentication infrastructure (JWT cookies, `require_role`, `?next=` threading in login), and template patterns (admin_base.html, teacher_base.html as examples for student_base.html).

The main implementation work is: (1) a new `checkin.py` router with GET and POST endpoints, (2) a `student_base.html` template following the admin/teacher pattern, (3) a `checkin.html` template with the centered card layout, and (4) tests covering the 7 CHKIN requirements. A critical integration detail is that `get_current_user` currently redirects to `/login` without preserving `?next=` -- the check-in GET endpoint must handle unauthenticated users by redirecting to `/login?next=/checkin?token=X` itself rather than relying on the dependency.

**Primary recommendation:** Create `app/routers/checkin.py` with dedicated check-in logic, `student_base.html` extending `base.html`, and `checkin.html` extending `student_base.html`. Handle auth redirect manually in the GET endpoint to preserve the token query parameter.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Minimal display: Raum (from Device) and Zeitraum (start_time-end_time) only. No subject, no teacher name, no class.
- **D-02:** After successful check-in, show confirmation message on the same page.
- **D-03:** If already checked in, show time of check-in instead of confirm button (e.g., "Eingecheckt um 08:02").
- **D-04:** GET `/checkin?token=X` requires authentication. If not authenticated, redirect to `/login?next=/checkin?token=X`. Uses existing `?next=` wiring from Phase 2 D-09.
- **D-05:** Only students can check in. Non-student roles see an error message.
- **D-06:** Check-in page has a single "Anwesenheit bestaetigen" button. POST writes the AttendanceRecord and shows confirmation.
- **D-07:** Expired token: "Diese Stunde ist bereits beendet."
- **D-08:** Invalid or missing token: "Ungultiger oder fehlender Token."
- **D-09:** Duplicate check-in: "Sie haben sich bereits eingecheckt." + show check-in time: "Eingecheckt um HH:MM"
- **D-10:** Non-student role: "Nur Schueler koennen sich einchecken."
- **D-11:** Inactive token: "Dieser Token ist nicht mehr gueltig."
- **D-12:** All errors displayed in the same centered card layout as the check-in page.
- **D-13:** Create `student_base.html` extending `base.html` with student nav: SmartAttend brand + Abmelden button. Same pattern as `admin_base.html` and `teacher_base.html`.
- **D-14:** Check-in template extends `student_base.html`. Centered `<article>` card (max-width 480px).
- **D-15:** Student router at `app/routers/student.py` with prefix -- or add check-in routes to a new `app/routers/checkin.py`. Claude decides structure.

### Claude's Discretion
- Router file organization (checkin.py vs extending existing auth.py student route)
- Exact template structure and Jinja2 blocks
- Whether to update the existing `/student` landing page to use the new `student_base.html`
- POST endpoint URL path (`/checkin` vs `/checkin/confirm`)
- Token validation order (check existence -> check active -> check expiry -> check duplicate)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CHKIN-01 | GET `/checkin?token=<uuid>` renders a page showing lesson info | Router GET endpoint + join chain AttendanceToken -> ScheduleEntry -> Device for room + times |
| CHKIN-02 | Page shows a login form (or uses existing session cookie) | Custom auth check in GET handler redirecting to `/login?next=` with token preserved |
| CHKIN-03 | POST `/checkin` validates token: exists, active, not expired | Token validation chain: existence -> is_active -> expires_at comparison |
| CHKIN-04 | POST `/checkin` rejects duplicate check-in for same student + lesson | Query AttendanceRecord for student_id + token_id before insert; DB UniqueConstraint as safety net |
| CHKIN-05 | POST `/checkin` writes an AttendanceRecord on success and shows confirmation | Create AttendanceRecord row, re-render template with success state |
| CHKIN-06 | Expired token shows clear error message | `datetime.now() > token.expires_at` check with German message D-07 |
| CHKIN-07 | Invalid token shows appropriate error | Token not found or missing query param, German message D-08 |
</phase_requirements>

## Architecture Patterns

### Recommended Project Structure
```
app/
  routers/
    checkin.py          # NEW: GET /checkin + POST /checkin
  templates/
    student_base.html   # NEW: extends base.html, student nav
    checkin.html         # NEW: extends student_base.html, centered card
```

### Pattern 1: Router File Organization
**What:** Dedicated `app/routers/checkin.py` (no prefix) for check-in routes.
**Why:** The `/checkin` URL must be short since it's embedded in NFC tag URLs. A separate router keeps concerns clean. The existing `/student` landing page in `auth.py` can be left as-is or migrated later.
**Registration in main.py:**
```python
from app.routers.checkin import router as checkin_router
app.include_router(checkin_router)
```

### Pattern 2: Manual Auth Check with ?next= Preservation
**What:** The GET `/checkin` endpoint cannot use `Depends(get_current_user)` directly because `get_current_user` redirects to `/login` without the `?next=` parameter. Instead, the endpoint must manually check authentication and redirect with the full return URL.
**Why:** D-04 requires redirecting to `/login?next=/checkin?token=X` so after login the student lands back on the check-in page.
**Implementation approach:**
```python
from fastapi import Cookie, Query, Request
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from urllib.parse import urlencode

@router.get("/checkin")
async def checkin_page(
    request: Request,
    token: str = Query(default=""),
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    # 1. Validate token param exists
    if not token:
        return templates.TemplateResponse(
            request=request,
            name="checkin.html",
            context={"error": "Ungültiger oder fehlender Token."},
        )

    # 2. Check authentication manually (mirror get_current_user logic)
    user = _get_user_from_cookie(access_token, db)
    if user is None:
        next_url = f"/checkin?token={token}"
        return RedirectResponse(
            url=f"/login?next={next_url}",
            status_code=303,
        )

    # 3. Check role
    if user.role != "student":
        return templates.TemplateResponse(...)

    # 4. Look up token, validate, render
    ...
```

**Alternative considered:** Passing `Request` into `get_current_user` to extract the URL -- rejected because it would require modifying a shared dependency used by all routes.

### Pattern 3: Token Validation Order
**What:** Validate in this order: existence -> is_active -> expiry -> duplicate check-in.
**Why:** Each step returns a distinct German error message (D-07 through D-11). Early return on first failure.
```python
# 1. Token existence
db_token = db.query(AttendanceToken).filter(AttendanceToken.token == token_str).first()
if not db_token:
    # D-08: "Ungültiger oder fehlender Token."

# 2. Token active
if not db_token.is_active:
    # D-11: "Dieser Token ist nicht mehr gültig."

# 3. Token not expired
if datetime.now() > db_token.expires_at:
    # D-07: "Diese Stunde ist bereits beendet."

# 4. Duplicate check
existing = db.query(AttendanceRecord).filter(
    AttendanceRecord.student_id == user.id,
    AttendanceRecord.token_id == db_token.id,
).first()
if existing:
    # D-09: "Sie haben sich bereits eingecheckt." + "Eingecheckt um HH:MM"
```

### Pattern 4: Template Inheritance (student_base.html)
**What:** Follow the exact pattern from `teacher_base.html` -- extends `base.html`, adds nav with brand + Abmelden, provides `{% block student_content %}`.
**Source:** `app/templates/teacher_base.html` (lines 1-17) and `admin_base.html` (lines 1-27).
```html
{% extends "base.html" %}
{% block content %}
<nav>
  <ul><li><strong>SmartAttend</strong></li></ul>
  <ul>
    <li>
      <form method="post" action="/auth/logout" style="margin: 0;">
        <button type="submit" class="outline secondary"
                style="margin: 0; padding: 0.5rem 1rem;">Abmelden</button>
      </form>
    </li>
  </ul>
</nav>
{% block student_content %}{% endblock %}
{% endblock %}
```

### Pattern 5: Centered Card Layout (checkin.html)
**What:** Reuse the centered `<article>` pattern from `login.html` and `student.html`.
**Source:** `app/templates/student.html` (line 4): `<article style="max-width: 480px; margin: 2rem auto;">`
```html
{% extends "student_base.html" %}
{% block student_content %}
<article style="max-width: 480px; margin: 2rem auto;">
  {% if error %}
    <p role="alert" style="color: var(--pico-del-color)">{{ error }}</p>
  {% elif success %}
    <p role="alert" style="color: #2e7d32">Anwesenheit erfolgreich erfasst.</p>
  {% else %}
    <hgroup>
      <h2>Anwesenheit erfassen</h2>
      <p>{{ room }} &mdash; {{ start_time }}–{{ end_time }}</p>
    </hgroup>
    <form method="post" action="/checkin">
      <input type="hidden" name="token" value="{{ token }}">
      <button type="submit">Anwesenheit bestätigen</button>
    </form>
  {% endif %}
</article>
{% endblock %}
```

### Pattern 6: POST Endpoint
**What:** POST `/checkin` receives token via hidden form field, validates, writes record, re-renders with success/error.
**Why:** Using POST for the state-changing action (writing AttendanceRecord) follows the existing pattern. Re-rendering the same template (not redirecting) matches D-02 and avoids exposing a separate confirmation URL.
```python
@router.post("/checkin")
async def checkin_confirm(
    request: Request,
    token: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("student")),
):
    # Validate token chain (same as GET but for POST)
    # Write AttendanceRecord
    record = AttendanceRecord(
        student_id=user.id,
        token_id=db_token.id,
        checked_in_at=datetime.now(),
    )
    db.add(record)
    db.commit()
    # Re-render with success=True
```

**Note:** POST can use `require_role("student")` because if the student was authenticated enough to see the form, their session is valid. The 303 redirect from `get_current_user` is acceptable here since POST is only called from the form.

### Anti-Patterns to Avoid
- **Using GET for state changes:** The check-in write MUST be POST, not GET. GET should only display the form.
- **Relying on DB constraint alone for duplicates:** While UniqueConstraint(student_id, token_id) exists, always check in application code first to provide a user-friendly German error message instead of a 500 IntegrityError.
- **URL-encoding the next parameter:** The `?next=/checkin?token=X` URL contains a nested query param. Keep it simple -- the login form's hidden `next` field already handles this correctly as a single string value.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JWT cookie verification | Custom cookie parsing | Mirror `get_current_user` logic from `app/dependencies.py` | Must stay in sync with auth system |
| Duplicate check-in detection | Application-only check | Application check + DB UniqueConstraint (already exists) | Belt and suspenders -- app check for UX, DB constraint for safety |
| Date/time formatting | Custom format strings | `strftime("%H:%M")` | Standard Python, consistent with existing code |

## Common Pitfalls

### Pitfall 1: get_current_user Breaks ?next= Flow
**What goes wrong:** Using `Depends(get_current_user)` on GET `/checkin` redirects unauthenticated users to `/login` without preserving `?token=X`. After login, the student lands on `/student` instead of the check-in page.
**Why it happens:** `get_current_user` raises HTTPException(303, Location="/login") with no `?next=` parameter.
**How to avoid:** Manually check authentication in the GET handler and construct the redirect URL with `?next=/checkin?token=X`.
**Warning signs:** After login, student doesn't see the check-in page.

### Pitfall 2: IntegrityError on Duplicate Check-in
**What goes wrong:** If the application-level duplicate check is skipped, a duplicate POST hits the UniqueConstraint and raises `IntegrityError`, which FastAPI renders as a 500 Internal Server Error.
**Why it happens:** Race condition or missing application check.
**How to avoid:** Always query for existing AttendanceRecord before inserting. Wrap the insert in a try/except IntegrityError as a safety net.
**Warning signs:** 500 errors on double-click of the confirm button.

### Pitfall 3: Expired Token Timing with datetime.now()
**What goes wrong:** `expires_at` is stored as a naive datetime. Using `datetime.utcnow()` or timezone-aware `datetime.now(tz=...)` would cause mismatches.
**Why it happens:** Mixing aware and naive datetimes.
**How to avoid:** Use `datetime.now()` (naive, local time) consistently, matching the existing pattern in `conftest.py` seed_token fixture (line 213: `expires_at=datetime.now() + timedelta(hours=2)`).
**Warning signs:** Tokens appearing expired when they shouldn't be, or vice versa.

### Pitfall 4: SQLAlchemy Session Visibility in Tests
**What goes wrong:** After `db.commit()` in the handler, the test's `db_session` may not see the new record without `db_session.refresh()`.
**Why it happens:** SQLite in-memory with StaticPool -- known issue documented in Phase 3 decisions.
**How to avoid:** In tests, after the POST call, query through the same `db_session` and call `refresh()` if checking object attributes.
**Warning signs:** Test assertions fail even though the endpoint returned success.

### Pitfall 5: Token Query Parameter with Special Characters
**What goes wrong:** UUID tokens are safe, but if the `?next=` URL contains the `?token=` param, URL encoding can mangle it.
**Why it happens:** Nested query parameters in the redirect URL.
**How to avoid:** The login form already passes `next` as a hidden form field value (not a URL param in the POST), so the value is preserved exactly. Just ensure the GET redirect uses proper URL construction.
**Warning signs:** Token value is truncated or empty after login redirect.

## Code Examples

### Join Chain for Room and Time Display
```python
# Source: Codebase models analysis
from sqlalchemy.orm import Session
from app.models.attendance_token import AttendanceToken
from app.models.schedule_entry import ScheduleEntry
from app.models.device import Device

db_token = db.query(AttendanceToken).filter(AttendanceToken.token == token_str).first()
entry = db.get(ScheduleEntry, db_token.schedule_entry_id)
device = db.get(Device, db_token.device_id)

room = device.room or "Unbekannt"
start_time = entry.start_time.strftime("%H:%M")
end_time = entry.end_time.strftime("%H:%M")
```

### Student Client Test Fixture
```python
# Pattern: follows admin_client and teacher_client from conftest.py
@pytest.fixture
def student_client(test_client, seed_students):
    """Authenticated TestClient as first seed student."""
    resp = test_client.post(
        "/auth/login",
        data={"email": "student1@test.com", "password": "studentpass", "next": ""},
    )
    assert resp.status_code == 303
    return test_client
```

### Helper Function for User Extraction from Cookie
```python
# Mirrors get_current_user logic but returns None instead of raising
def _get_user_from_cookie(access_token: str | None, db: Session) -> User | None:
    if access_token is None:
        return None
    try:
        payload = jwt.decode(access_token, get_settings().secret_key, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    user = db.get(User, int(user_id))
    if user is None or not user.is_active:
        return None
    return user
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | None (uses defaults, tests/ directory) |
| Quick run command | `python -m pytest tests/test_checkin.py -x` |
| Full suite command | `python -m pytest tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CHKIN-01 | GET /checkin?token=uuid renders lesson info (room, times) | integration | `python -m pytest tests/test_checkin.py::test_checkin_page_shows_lesson_info -x` | Wave 0 |
| CHKIN-02 | Unauthenticated user redirected to login with ?next= | integration | `python -m pytest tests/test_checkin.py::test_checkin_unauthenticated_redirects_to_login -x` | Wave 0 |
| CHKIN-03 | POST validates token: exists, active, not expired | integration | `python -m pytest tests/test_checkin.py::test_checkin_post_validates_token -x` | Wave 0 |
| CHKIN-04 | POST rejects duplicate check-in | integration | `python -m pytest tests/test_checkin.py::test_checkin_duplicate_rejected -x` | Wave 0 |
| CHKIN-05 | POST writes AttendanceRecord on success | integration | `python -m pytest tests/test_checkin.py::test_checkin_success_writes_record -x` | Wave 0 |
| CHKIN-06 | Expired token shows German error | integration | `python -m pytest tests/test_checkin.py::test_checkin_expired_token_error -x` | Wave 0 |
| CHKIN-07 | Invalid/missing token shows error | integration | `python -m pytest tests/test_checkin.py::test_checkin_invalid_token_error -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_checkin.py -x`
- **Per wave merge:** `python -m pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_checkin.py` -- covers CHKIN-01 through CHKIN-07
- [ ] `student_client` fixture in `tests/conftest.py` -- authenticated student test client

## Open Questions

1. **Should `/student` landing page be updated to use `student_base.html`?**
   - What we know: Currently `student.html` extends `base.html` directly (no nav, no logout button).
   - What's unclear: Whether updating it now is worth the small risk of breaking the existing page.
   - Recommendation: Update it -- it's a one-line change (`extends "student_base.html"` + `block student_content`) and gives students consistent navigation. Low risk.

2. **Should the POST endpoint use `/checkin` or `/checkin/confirm`?**
   - What we know: Both work. `/checkin` is simpler and the form method (POST vs GET) disambiguates.
   - Recommendation: Use `/checkin` for both GET and POST. Same URL, different methods -- standard pattern.

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `app/models/attendance_token.py`, `app/models/attendance_record.py`, `app/models/schedule_entry.py`, `app/models/device.py`
- Codebase analysis: `app/dependencies.py` -- get_current_user and require_role implementations
- Codebase analysis: `app/routers/auth.py` -- login flow with ?next= threading
- Codebase analysis: `app/templates/admin_base.html`, `teacher_base.html`, `student.html`, `login.html` -- template patterns
- Codebase analysis: `tests/conftest.py` -- fixture patterns including seed_token, seed_students, admin_client

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in use, no new dependencies needed
- Architecture: HIGH -- follows established patterns from Phase 2/3/4 exactly
- Pitfalls: HIGH -- identified from direct codebase analysis of get_current_user behavior and SQLAlchemy session patterns

**Research date:** 2026-03-29
**Valid until:** 2026-04-28 (stable -- no external dependencies, internal codebase patterns only)
