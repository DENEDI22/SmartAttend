# Phase 2: Authentication - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver JWT-based login/logout with HTTP-only cookie, role-based route protection (`require_role` dependency), and the login page UI. Includes an env-var-seeded admin account created on first boot.

Does NOT include the full check-in flow (Phase 5) — but DOES include the `?next=` redirect wiring so the check-in page can return students to their token URL after login, and a student landing placeholder page.

</domain>

<decisions>
## Implementation Decisions

### Login Identifier
- **D-01:** Login uses `email` as the identifier — no separate `username` field. User model already has `email` (unique, indexed). The login form label will be "E-Mail".

### Cookie & JWT
- **D-02:** JWT stored in an HTTP-only cookie (locked from Phase 1 / PROJECT.md).
- **D-03:** Expiry: 8 hours for admin/teacher, 1 hour for students (locked from Phase 1 / PROJECT.md).
- **D-04:** Cookie settings: `httponly=True`, `samesite="lax"`, `secure=False` (HTTP-only RPi deployment). Cookie name: `access_token`.

### Auth Failure UX
- **D-05:** Failed login renders an inline flash/alert on the same `/login` page — pass an `error` variable to the Jinja2 template. No redirect, no JS.
- **D-06:** All error messages on the login page are in **German** (consistent with CHKIN-06 German error messages). E.g. "Ungültige E-Mail oder Passwort."
- **D-07:** Accessing a protected route without a valid cookie → redirect to `/login` with a 303 (not 401 JSON). API semantics are secondary to browser UX for this app.

### Post-Login Redirects
- **D-08:** After successful login, redirect based on role:
  - `admin` → `/admin`
  - `teacher` → `/teacher`
  - `student` → see D-09
- **D-09:** Student redirect logic (two cases):
  1. **With `?next=` param** (came from check-in flow): redirect to `next` URL after login. This is how the check-in flow will re-authenticate a student mid-way. The `?next=` param must be threaded from the login GET through the login POST.
  2. **Without `?next=`** (student navigated directly to `/login`): redirect to `/student` — a placeholder landing page ("Bitte Gerät antippen, um Anwesenheit zu erfassen"). Full check-in logic is Phase 5; Phase 2 just delivers the placeholder and the redirect routing.
- **D-10:** `?next=` redirect is **students-only** — admin and teacher always go to their fixed destinations regardless of any `?next=` param (avoids open-redirect risk for privileged roles).

### Role Enforcement
- **D-11:** `require_role(*roles)` FastAPI dependency:
  - No cookie / invalid JWT → redirect to `/login` (303)
  - Valid JWT but wrong role → return 403 (no redirect — caller made a deliberate wrong-role request)
- **D-12:** The dependency lives in `app/dependencies.py` (or `app/auth/dependencies.py`). Returns the current `User` ORM object for use in route handlers.

### Admin Bootstrap
- **D-13:** If `ADMIN_EMAIL` and `ADMIN_PASSWORD` are set in `.env`, the server creates an admin user on first boot (inside the FastAPI lifespan) if no admin user exists yet. Idempotent — repeated restarts do not duplicate the account.
- **D-14:** Add `ADMIN_EMAIL` and `ADMIN_PASSWORD` to `.env.example` with placeholder values.

### Claude's Discretion
- Exact Jinja2 template structure for `/login` — layout, field ordering, form action. Use Pico CSS semantic form elements.
- Password hashing: use `passlib[bcrypt]` (already in requirements.txt). Claude picks the scheme name ("bcrypt").
- JWT library: `python-jose[cryptography]` (already in requirements.txt). Claude picks the algorithm ("HS256").
- Cookie `max_age` value alignment with the JWT `exp` claim (they should match).
- Structure of `app/routers/auth.py` vs `app/auth/` subpackage — Claude picks what stays clean.
- Student landing page content and styling — brief, in German, tells students to tap the NFC device.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — AUTH-01 through AUTH-07 define all Phase 2 acceptance criteria

### Project Context
- `.planning/PROJECT.md` — Tech stack constraints, JWT cookie decision (8h/1h), Pico CSS constraint
- `.planning/phases/01-foundation/01-CONTEXT.md` — User model fields (D-04), established patterns

No external specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/models/user.py` — User model with `email`, `password_hash`, `role`, `is_active`, `class_name`
- `app/database.py` — `get_db()` session dependency pattern to follow
- `app/config.py` — `get_settings()` lru_cache pattern; new `ADMIN_EMAIL`/`ADMIN_PASSWORD` fields go here
- `app/main.py` — lifespan function where admin seed logic runs; router includes go here

### Established Patterns
- SQLAlchemy 2.0 `Mapped[]` typed columns (from Phase 1)
- pydantic-settings `SettingsConfigDict` for config (from Phase 1)
- `app/routers/` for route modules, `app/services/` for business logic

### Integration Points
- `app/main.py` — include `app.routers.auth` router with prefix `/auth`
- `app/main.py` lifespan — add admin seed call after `create_all()`
- Templates: `app/templates/` — currently empty (`.gitkeep`); Phase 2 creates first templates
- Static: `app/static/` — Pico CSS file must be added here (served via `StaticFiles`)

</code_context>

<specifics>
## Specific Ideas

- Student redirect with `?next=` param is the bridge to Phase 5 check-in: the check-in page will redirect unauthenticated students to `/login?next=/checkin?token=<uuid>`, and after login they return to complete check-in.
- Student landing page is a placeholder in Phase 2 — Phase 5 replaces or supplements it with the full check-in UI.
- All UI text visible to students/teachers/admins should be in German where it touches end-user messages.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-authentication*
*Context gathered: 2026-03-27*
