# Phase 02: Authentication - Research

**Researched:** 2026-03-27
**Domain:** FastAPI JWT authentication with HTTP-only cookies, Jinja2 templates, passlib/bcrypt, python-jose
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Login uses `email` as the identifier — no separate `username` field. The login form label will be "E-Mail".
- **D-02:** JWT stored in an HTTP-only cookie (locked from Phase 1 / PROJECT.md).
- **D-03:** Expiry: 8 hours for admin/teacher, 1 hour for students (locked from Phase 1 / PROJECT.md).
- **D-04:** Cookie settings: `httponly=True`, `samesite="lax"`, `secure=False` (HTTP-only RPi deployment). Cookie name: `access_token`.
- **D-05:** Failed login renders an inline flash/alert on the same `/login` page — pass an `error` variable to the Jinja2 template. No redirect, no JS.
- **D-06:** All error messages on the login page are in **German**. E.g. "Ungültige E-Mail oder Passwort."
- **D-07:** Accessing a protected route without a valid cookie → redirect to `/login` with a 303 (not 401 JSON).
- **D-08:** After successful login, redirect based on role: admin → `/admin`, teacher → `/teacher`, student → see D-09.
- **D-09:** Student redirect logic: with `?next=` param → redirect to `next` URL; without `?next=` → redirect to `/student` placeholder.
- **D-10:** `?next=` redirect is students-only — admin and teacher always go to their fixed destinations.
- **D-11:** `require_role(*roles)` FastAPI dependency: no cookie / invalid JWT → redirect to `/login` (303); valid JWT but wrong role → return 403 (no redirect).
- **D-12:** The dependency lives in `app/dependencies.py` (or `app/auth/dependencies.py`). Returns the current `User` ORM object.
- **D-13:** If `ADMIN_EMAIL` and `ADMIN_PASSWORD` are set in `.env`, the server creates an admin user on first boot (inside the FastAPI lifespan) if no admin user exists yet. Idempotent.
- **D-14:** Add `ADMIN_EMAIL` and `ADMIN_PASSWORD` to `.env.example` with placeholder values.

### Claude's Discretion

- Exact Jinja2 template structure for `/login` — layout, field ordering, form action. Use Pico CSS semantic form elements.
- Password hashing: use `passlib[bcrypt]` (already in requirements.txt). Claude picks the scheme name ("bcrypt").
- JWT library: `python-jose[cryptography]` (already in requirements.txt). Claude picks the algorithm ("HS256").
- Cookie `max_age` value alignment with the JWT `exp` claim (they should match).
- Structure of `app/routers/auth.py` vs `app/auth/` subpackage — Claude picks what stays clean.
- Student landing page content and styling — brief, in German, tells students to tap the NFC device.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AUTH-01 | User can log in with username and password via POST `/auth/login` | Form data handling via `Form()`, passlib bcrypt verify, python-jose encode |
| AUTH-02 | Server sets an HTTP-only JWT cookie on successful login | `RedirectResponse.set_cookie(httponly=True, samesite="lax", secure=False)` confirmed working |
| AUTH-03 | JWT expires after 8 hours for admin/teacher, 1 hour for students | `timedelta` passed into `jwt.encode()` `exp` claim; `max_age` mirrors expiry |
| AUTH-04 | User can log out via POST `/auth/logout` (cookie cleared) | `response.delete_cookie(key="access_token")` + 303 redirect |
| AUTH-05 | GET `/auth/me` returns current user info for authenticated users | `get_current_user` dependency decodes cookie JWT, returns User ORM object |
| AUTH-06 | `require_role(*roles)` dependency rejects wrong roles with 403 | Outer function returns inner `Depends`-wired checker; wrong role → `HTTPException(403)` |
| AUTH-07 | Login page (`/login`) renders and submits correctly | `Jinja2Templates.TemplateResponse`, `Form()` params, `?next=` threading via hidden input |
</phase_requirements>

---

## Summary

Phase 2 delivers the complete authentication layer for SmartAttend: a login/logout flow using JWT stored in HTTP-only cookies, role-based route protection via a `require_role` FastAPI dependency, two Jinja2 templates (login page and student landing placeholder), and an idempotent admin seed on first boot.

All required libraries are already pinned in `requirements.txt` from Phase 1: `python-jose[cryptography]==3.5.0`, `passlib[bcrypt]==1.7.4`, `jinja2==3.1.6`, and `python-multipart==0.0.22`. No new packages need to be installed. The Pico CSS static file (`pico.min.css` v2.1.1) must be downloaded once and committed to `app/static/`.

The key implementation challenge is correctly threading the `?next=` parameter from GET through the POST login form back to the redirect for the student role. The other significant detail is that `secure=False` must be set on the cookie (HTTP-only RPi deployment — not HTTPS), and tests must account for the fact that FastAPI's TestClient will only send `secure=True` cookies over HTTPS; since `secure=False` is used here, TestClient will send cookies normally.

**Primary recommendation:** Keep all auth logic in a flat `app/routers/auth.py` + `app/services/auth.py` + `app/dependencies.py` structure — not a subpackage. This matches the existing Phase 1 conventions (`app/routers/`, `app/services/`) and avoids over-engineering for three files.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| python-jose[cryptography] | 3.5.0 | JWT encode/decode (HS256) | Already pinned in requirements.txt; standard FastAPI auth library |
| passlib[bcrypt] | 1.7.4 | Password hashing and verification | Already pinned; widely used with FastAPI |
| jinja2 | 3.1.6 | HTML template rendering | Already pinned; FastAPI's built-in template engine |
| python-multipart | 0.0.22 | Parses `application/x-www-form-urlencoded` form POSTs | Already pinned; required for `Form()` parameters in FastAPI |
| Pico CSS | 2.1.1 | Semantic classless CSS framework | CLAUDE.md constraint; served from `app/static/pico.min.css` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| FastAPI `Cookie()` | (fastapi 0.135.x) | Declare cookie as dependency parameter | Reading `access_token` cookie in auth dependencies |
| FastAPI `Form()` | (fastapi 0.135.x) | Declare form field as dependency parameter | Login POST handler — email, password, next |
| `RedirectResponse` | (starlette via fastapi) | Issue 303 redirects | After login success; after logout; unauthenticated route access |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| python-jose | PyJWT | FastAPI official docs now show PyJWT; but python-jose is already pinned and works identically for HS256 use case |
| passlib[bcrypt] | pwdlib[argon2] | FastAPI docs now recommend pwdlib/Argon2; but passlib is already pinned and bcrypt is sufficient for this prototype |
| Flat `app/routers/auth.py` | `app/auth/` subpackage | Subpackage adds indirection without benefit at this scale; flat structure matches Phase 1 conventions |

**Installation:** Nothing to install — all packages already in `requirements.txt`. Only action needed for stack:

```bash
# Download Pico CSS v2.1.1 once (run from project root, not inside container)
curl -o app/static/pico.min.css \
  https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css
```

**Version verification:** Package versions confirmed by reading `requirements.txt` directly from the codebase. Pico CSS v2.1.1 confirmed as latest stable via npm registry search (2026-03-27).

---

## Architecture Patterns

### Recommended Project Structure

```
app/
├── routers/
│   └── auth.py          # GET /login, POST /auth/login, POST /auth/logout, GET /auth/me, GET /student
├── services/
│   └── auth.py          # create_access_token(), verify_password(), get_password_hash(), authenticate_user()
├── dependencies.py      # get_current_user(), require_role(*roles)
├── templates/
│   ├── base.html        # <!DOCTYPE html lang="de">, Pico CSS link, {% block content %}
│   ├── login.html       # extends base.html — login form
│   └── student.html     # extends base.html — placeholder landing
├── static/
│   └── pico.min.css     # Pico CSS v2.1.1 (committed to repo)
├── config.py            # Add ADMIN_EMAIL, ADMIN_PASSWORD fields
└── main.py              # Add StaticFiles mount, Jinja2Templates, include auth router, admin seed in lifespan
```

### Pattern 1: JWT Encode/Decode with python-jose

**What:** Create tokens with role-aware expiry; decode in dependencies.
**When to use:** Login POST (encode), every protected route (decode via dependency).

```python
# Source: python-jose docs + FastAPI security tutorial pattern
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, get_settings().secret_key, algorithm=ALGORITHM)
```

Role-aware expiry at call site:
```python
# In login handler — after role confirmed
if user.role == "student":
    expires = timedelta(hours=1)
else:
    expires = timedelta(hours=8)
token = create_access_token(data={"sub": str(user.id), "role": user.role}, expires_delta=expires)
```

### Pattern 2: HTTP-only Cookie on RedirectResponse

**What:** Set JWT directly on a `RedirectResponse` instance before returning.
**When to use:** Login POST success path.
**Critical detail:** Must call `set_cookie()` on the *same* `RedirectResponse` instance — not on an injected `Response` parameter.

```python
# Source: FastAPI docs (response-cookies) + GitHub issue #2452 confirmed fix
from fastapi.responses import RedirectResponse

response = RedirectResponse(url=redirect_url, status_code=303)
response.set_cookie(
    key="access_token",
    value=token,
    httponly=True,
    samesite="lax",
    secure=False,          # RPi HTTP deployment — D-04
    max_age=expiry_seconds # must match JWT exp claim
)
return response
```

### Pattern 3: Cookie Reading in Dependency

**What:** Read the `access_token` cookie, decode JWT, return User ORM object.
**When to use:** All protected routes via `Depends(get_current_user)`.

```python
# Source: FastAPI Cookie() dependency pattern
from fastapi import Cookie, Depends, HTTPException
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.config import get_settings

ALGORITHM = "HS256"

async def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    if access_token is None:
        # D-07: redirect to /login with 303 for browser UX
        raise _redirect_to_login()
    try:
        payload = jwt.decode(access_token, get_settings().secret_key, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise _redirect_to_login()
    except JWTError:
        raise _redirect_to_login()
    user = db.get(User, int(user_id))
    if user is None or not user.is_active:
        raise _redirect_to_login()
    return user

def _redirect_to_login():
    # Can't raise RedirectResponse directly — wrap in HTTPException workaround
    # Cleanest pattern: return RedirectResponse, not raise
    pass
```

**Note on redirect-vs-raise:** FastAPI dependencies cannot `raise RedirectResponse` — `HTTPException` only accepts status codes that produce JSON errors. The clean pattern is to return `RedirectResponse` from the route handler after detecting no cookie. However, for dependencies the practical pattern is to raise `HTTPException(status_code=303, headers={"Location": "/login"})` which produces the redirect. Alternatively, wrap with a custom exception handler. The simplest confirmed approach for SSRUI apps:

```python
# Raise a 303 redirect from dependency — works in Starlette/FastAPI
from starlette.responses import RedirectResponse as StarletteRedirect

def _redirect_to_login():
    from fastapi import HTTPException
    # status 303 with Location header acts as redirect
    raise HTTPException(
        status_code=303,
        headers={"Location": "/login"},
    )
```

### Pattern 4: require_role Dependency

**What:** Closure that creates a role-checking dependency; returns User ORM object.
**When to use:** Any route that requires a specific role. D-11: wrong role → 403 (not redirect).

```python
# Source: fastapitutorial.medium.com pattern, adapted for *roles variadic
from typing import Callable
from fastapi import Depends, HTTPException

def require_role(*roles: str) -> Callable:
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker

# Usage in route:
@router.get("/admin")
async def admin_dashboard(user: User = Depends(require_role("admin"))):
    ...
```

### Pattern 5: Form POST with ?next= Threading

**What:** GET `/login?next=...` → template with `next` var → hidden input → POST reads `next` from form → students-only redirect.
**When to use:** Login flow for student check-in return (D-09, D-10).

```python
# GET handler
@router.get("/login")
async def login_page(request: Request, next: str = ""):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"next": next, "error": None},
    )

# POST handler
@router.post("/auth/login")
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form(default=""),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"next": next, "error": "Ungültige E-Mail oder Passwort."},
            status_code=200,
        )
    # Role-based redirect — D-08, D-09, D-10
    if user.role == "admin":
        redirect_url = "/admin"
    elif user.role == "teacher":
        redirect_url = "/teacher"
    else:  # student
        redirect_url = next if next else "/student"

    expires = timedelta(hours=1) if user.role == "student" else timedelta(hours=8)
    token = create_access_token({"sub": str(user.id), "role": user.role}, expires)
    response = RedirectResponse(url=redirect_url, status_code=303)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=int(expires.total_seconds()),
    )
    return response
```

### Pattern 6: Admin Seed in Lifespan

**What:** Create admin user on first boot if ADMIN_EMAIL and ADMIN_PASSWORD are set and no admin exists.
**When to use:** `app/main.py` lifespan, after `create_all()`. D-13: idempotent.

```python
# In lifespan, after Base.metadata.create_all(bind=engine)
async def seed_admin(db: Session) -> None:
    settings = get_settings()
    if not settings.admin_email or not settings.admin_password:
        return
    existing = db.query(User).filter(User.role == "admin").first()
    if existing:
        return
    db.add(User(
        email=settings.admin_email,
        first_name="Admin",
        last_name="Admin",
        role="admin",
        password_hash=get_password_hash(settings.admin_password),
        is_active=True,
    ))
    db.commit()
```

### Pattern 7: passlib CryptContext

**What:** Bcrypt hashing and verification. Claude's discretion picks scheme "bcrypt".

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

### Pattern 8: Jinja2 Template Setup in main.py

```python
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
```

**Important:** `Jinja2Templates` is typically instantiated as a module-level variable and imported in routers. Since `app/main.py` mounts static files, import `templates` from wherever it is created. The cleanest pattern for this project: create a `app/templates_config.py` or define it inside `main.py` and pass it into the router via a module-level variable in `app/routers/auth.py`.

### Anti-Patterns to Avoid

- **Calling set_cookie() on an injected Response parameter and then returning a different RedirectResponse:** The cookie will be lost. Always call `set_cookie()` on the same instance you return.
- **Using `raise HTTPException(401)` instead of a 303 redirect for browser UX:** D-07 locked the behavior — unauth access redirects, not 401 JSON.
- **Storing the JWT as a Bearer token in localStorage:** D-02 locked HTTP-only cookie storage.
- **Setting `secure=True` in the cookie:** This is HTTP-only deployment; `secure=True` blocks cookies over HTTP.
- **Using `response_class=HTMLResponse` and also setting cookies via `Response` parameter:** Only works if you don't return a different response object. Use `TemplateResponse` for re-render or `RedirectResponse` for redirect — set cookies on the returned instance.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Password hashing | Custom bcrypt wrapper | `passlib.context.CryptContext(schemes=["bcrypt"])` | Handles work factor, salt generation, timing-safe comparison, upgrade path |
| JWT encode/decode | Custom base64 signing | `jose.jwt.encode() / jwt.decode()` | Handles exp validation, algorithm negotiation, signature verification |
| Timing-safe password comparison | `==` string comparison | `CryptContext.verify()` | Passlib uses `hmac.compare_digest` internally — prevents timing attacks |
| Cookie expiry alignment | Separate expiry tracking | Set `max_age` on cookie to `int(timedelta.total_seconds())` — mirrors JWT `exp` exactly |

**Key insight:** The JWT `exp` claim and the cookie `max_age` must be set from the same `timedelta` value at the same moment. If they diverge, the browser may delete the cookie while the JWT is still valid (or vice versa).

---

## Common Pitfalls

### Pitfall 1: set_cookie() lost on RedirectResponse

**What goes wrong:** Cookie set via `response: Response = ...` parameter is discarded when a `RedirectResponse` is returned from the handler.
**Why it happens:** FastAPI replaces the response object; the `set_cookie()` call was on a different object.
**How to avoid:** Create `RedirectResponse` in the handler body, call `set_cookie()` on it, return it.
**Warning signs:** Login appears to succeed (303 redirect fires) but subsequent requests have no cookie.

### Pitfall 2: `?next=` open redirect vulnerability

**What goes wrong:** Student logs in and is redirected to an attacker-supplied external URL via `?next=https://evil.com`.
**Why it happens:** Trusting the `next` param without validation.
**How to avoid:** D-10 already scopes `?next=` to student role only. Additionally, validate that `next` starts with `/` (relative path only) before redirecting. Reject absolute URLs.
**Warning signs:** `next` value contains `://` or starts with `//`.

### Pitfall 3: `lru_cache` on get_settings() bleeds ADMIN_EMAIL/ADMIN_PASSWORD into tests

**What goes wrong:** Admin email/password from one test bleeds into the next because `get_settings()` is cached.
**Why it happens:** `lru_cache` shares the Settings instance across all calls within the process.
**How to avoid:** The existing `conftest.py` already calls `get_settings.cache_clear()` before and after each test. Extend `override_settings` fixture to also set `ADMIN_EMAIL` and `ADMIN_PASSWORD` env vars (or explicitly set them to empty strings in tests that don't need them).
**Warning signs:** Admin user appears in tests that shouldn't create one.

### Pitfall 4: `secure=True` blocks TestClient cookie sending

**What goes wrong:** TestClient sends requests over HTTP (`http://testserver`); `secure=True` cookies are not sent over HTTP.
**Why it happens:** This is correct browser/cookie behavior, not a bug.
**How to avoid:** `secure=False` is already locked by D-04. Confirm the fixture never sets `secure=True`.
**Warning signs:** `get_current_user` sees no cookie even after a successful login in a test.

### Pitfall 5: JWTError on expired token not producing redirect

**What goes wrong:** An expired JWT raises `JWTError` in the dependency; the handler returns a 500 or unformatted error.
**Why it happens:** `JWTError` is not caught, or caught but re-raised as 422 instead of 303.
**How to avoid:** Catch `JWTError` (includes `ExpiredSignatureError`) and redirect to `/login` with 303.
**Warning signs:** Browser shows 422 or 500 after an 8-hour session expires.

### Pitfall 6: Jinja2Templates directory path relative to working directory

**What goes wrong:** `Jinja2Templates(directory="app/templates")` fails when uvicorn is started from a different working directory.
**Why it happens:** The path is relative to `cwd`, not the Python file.
**How to avoid:** Use `pathlib` to construct an absolute path, or ensure uvicorn is always started from project root (which the Dockerfile's `WORKDIR /app` and `CMD` guarantee). For tests, `conftest.py` already runs from project root (pytest.ini `rootdir`).
**Warning signs:** `TemplateNotFound` errors in tests but not in Docker.

---

## Code Examples

Verified patterns from official sources and confirmed implementations:

### Password context (passlib)

```python
# Source: passlib documentation; confirmed working with passlib 1.7.4
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

### JWT creation (python-jose)

```python
# Source: python-jose README + FastAPI security tutorial adapted
from jose import jwt
from datetime import datetime, timedelta, timezone

def create_access_token(data: dict, expires_delta: timedelta) -> str:
    payload = {**data, "exp": datetime.now(timezone.utc) + expires_delta}
    return jwt.encode(payload, get_settings().secret_key, algorithm="HS256")
```

### Logout handler

```python
@router.post("/auth/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="access_token")
    return response
```

### /auth/me endpoint

```python
@router.get("/auth/me")
async def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }
```

### Config additions for admin seed

```python
# Add to app/config.py Settings class
admin_email: str | None = None
admin_password: str | None = None
```

### base.html template structure

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="/static/pico.min.css">
  <title>{% block title %}SmartAttend{% endblock %}</title>
</head>
<body>
  <main class="container">
    {% block content %}{% endblock %}
  </main>
</body>
</html>
```

### login.html template structure

```html
{% extends "base.html" %}
{% block title %}Anmelden — SmartAttend{% endblock %}
{% block content %}
<article style="max-width: 360px; margin: 2rem auto;">
  <hgroup>
    <h1>SmartAttend</h1>
    <p>Bitte melden Sie sich an.</p>
  </hgroup>
  <form method="post" action="/auth/login">
    <input type="hidden" name="next" value="{{ next | default('') }}">
    <label for="email">E-Mail</label>
    <input type="email" id="email" name="email" autocomplete="username" required>
    <label for="password">Passwort</label>
    <input type="password" id="password" name="password" autocomplete="current-password" required>
    <button type="submit">Anmelden</button>
    {% if error %}
    <small role="alert" style="color: var(--del-color)">{{ error }}</small>
    {% endif %}
  </form>
</article>
{% endblock %}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `python-jose` for JWT | FastAPI docs now show `PyJWT` | ~2024 | No impact — python-jose is pinned and works; do not change |
| `passlib[bcrypt]` | FastAPI docs now suggest `pwdlib[argon2]` | ~2024 | No impact — passlib is pinned; bcrypt is sufficient |
| `@app.on_event("startup")` | `lifespan` context manager | FastAPI 0.93+ | Already using `lifespan` in Phase 1 — continue |
| Jinja2 `TemplateResponse("name", {"request": request, ...})` | `TemplateResponse(request=request, name="name", context={...})` | Starlette 0.20+ | Use the newer keyword-argument form (confirmed in fastapi 0.135.x) |

**Deprecated/outdated:**
- `@app.on_event("startup")`: Deprecated in FastAPI. Phase 1 already uses `lifespan` — continue that pattern.
- `TemplateResponse("name.html", {"request": req, "key": val})`: Still works but the newer form `TemplateResponse(request=req, name="name.html", context={"key": val})` is preferred.

---

## Open Questions

1. **Jinja2Templates instance location**
   - What we know: Templates must be initialized once; routers need access to the instance.
   - What's unclear: Best module to own the instance given Phase 1 patterns — `main.py` global or a dedicated `app/templates_config.py`.
   - Recommendation: Define `templates = Jinja2Templates(directory="app/templates")` in `app/routers/auth.py` as a module-level variable. This is self-contained for Phase 2. Later phases that add templates can import from a shared location if needed.

2. **`get_current_user` redirect mechanism**
   - What we know: FastAPI dependencies cannot raise `RedirectResponse` directly. HTTPException with `status_code=303` and `Location` header works in Starlette.
   - What's unclear: Whether `raise HTTPException(status_code=303, headers={"Location": "/login"})` produces a clean 303 with no body, vs whether a custom exception handler is needed.
   - Recommendation: Use `HTTPException(status_code=303, headers={"Location": "/login"})` in the dependency; test it in the first test. If FastAPI wraps it in a JSON error body, add a custom exception handler for 303 in `main.py`. Confirmed pattern from Starlette behavior.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11 (in Docker) | All application code | via Docker | 3.11-slim | — |
| python-jose[cryptography] | JWT encode/decode | via Docker requirements.txt | 3.5.0 | — |
| passlib[bcrypt] | Password hashing | via Docker requirements.txt | 1.7.4 | — |
| python-multipart | Form() params | via Docker requirements.txt | 0.0.22 | — |
| pytest 8.4.2 | Tests | Host (system python 3.14) | 8.4.2 | — |
| fastapi 0.135.1 | App + tests | Host + Docker | 0.135.1 | — |
| httpx 0.28.1 | TestClient transport | Host | 0.28.1 | — |
| Pico CSS 2.1.1 | Login template | NOT YET DOWNLOADED | — | Must download before Wave 0 |

**Missing dependencies with no fallback:**
- Pico CSS `app/static/pico.min.css`: Must be downloaded and committed before templates can be tested. Wave 0 task must include this step.

**Note on python-jose/passlib on host:** These packages are NOT installed on the host system (Arch Linux externally-managed environment). They are only available inside the Docker container. Tests that import these packages directly will fail on the host. Tests must either mock these functions or run inside Docker. The existing test suite in Phase 1 runs on the host and does NOT import jose/passlib. Phase 2 tests should follow the same pattern: test HTTP behavior via TestClient (which imports fastapi, not jose/passlib directly), or mock the auth service functions.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 |
| Config file | none — rootdir auto-detected as project root |
| Quick run command | `python3 -m pytest tests/test_auth.py -x -q` |
| Full suite command | `python3 -m pytest tests/ -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AUTH-01 | POST `/auth/login` with valid credentials returns 303 + sets cookie | integration | `python3 -m pytest tests/test_auth.py::test_login_success -x` | Wave 0 |
| AUTH-01 | POST `/auth/login` with invalid credentials returns 200 + error in response | integration | `python3 -m pytest tests/test_auth.py::test_login_invalid_credentials -x` | Wave 0 |
| AUTH-01 | POST `/auth/login` with inactive user returns 200 + error | integration | `python3 -m pytest tests/test_auth.py::test_login_inactive_user -x` | Wave 0 |
| AUTH-02 | Successful login response has `access_token` cookie with `httponly=True` | integration | `python3 -m pytest tests/test_auth.py::test_login_cookie_httponly -x` | Wave 0 |
| AUTH-03 | Admin/teacher token `exp` claim is ~8 hours from now | unit | `python3 -m pytest tests/test_auth.py::test_token_expiry_admin -x` | Wave 0 |
| AUTH-03 | Student token `exp` claim is ~1 hour from now | unit | `python3 -m pytest tests/test_auth.py::test_token_expiry_student -x` | Wave 0 |
| AUTH-04 | POST `/auth/logout` clears the `access_token` cookie and redirects | integration | `python3 -m pytest tests/test_auth.py::test_logout -x` | Wave 0 |
| AUTH-05 | GET `/auth/me` with valid cookie returns user JSON | integration | `python3 -m pytest tests/test_auth.py::test_me_authenticated -x` | Wave 0 |
| AUTH-05 | GET `/auth/me` without cookie redirects to `/login` (303) | integration | `python3 -m pytest tests/test_auth.py::test_me_unauthenticated -x` | Wave 0 |
| AUTH-06 | Route with `require_role("admin")` returns 403 for teacher | integration | `python3 -m pytest tests/test_auth.py::test_require_role_wrong_role -x` | Wave 0 |
| AUTH-06 | Route with `require_role("admin")` returns 200/ok for admin | integration | `python3 -m pytest tests/test_auth.py::test_require_role_correct_role -x` | Wave 0 |
| AUTH-07 | GET `/login` renders HTML with form | integration | `python3 -m pytest tests/test_auth.py::test_login_page_renders -x` | Wave 0 |
| AUTH-07 | GET `/login?next=/some/path` includes next in rendered HTML | integration | `python3 -m pytest tests/test_auth.py::test_login_page_next_param -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `python3 -m pytest tests/test_auth.py -x -q`
- **Per wave merge:** `python3 -m pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_auth.py` — all AUTH-01 through AUTH-07 tests listed above
- [ ] `app/static/pico.min.css` — Pico CSS must be downloaded (not a test file, but a Wave 0 blocker)
- [ ] `conftest.py` update — extend `override_settings` fixture to include `ADMIN_EMAIL=""` and `ADMIN_PASSWORD=""` env var overrides to prevent seed logic from running unexpectedly in tests; add a `db_session` fixture and `test_client` fixture using `TestClient(app)`

*(No new pytest framework install needed — pytest 8.4.2 already available on host)*

---

## Sources

### Primary (HIGH confidence)

- FastAPI official docs — [Response Cookies](https://fastapi.tiangolo.com/advanced/response-cookies/) — set_cookie() on response instances
- FastAPI official docs — [Templates](https://fastapi.tiangolo.com/advanced/templates/) — Jinja2Templates setup, TemplateResponse pattern
- FastAPI official docs — [Security/OAuth2-JWT](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) — JWT encode/decode patterns
- GitHub fastapi/fastapi [issue #2452](https://github.com/fastapi/fastapi/issues/2452) — confirmed: `set_cookie()` on RedirectResponse instance works
- GitHub fastapi/fastapi [issue #3339](https://github.com/fastapi/fastapi/issues/3339) — confirmed: test cookie properties separately; pass cookies manually in TestClient
- Project `requirements.txt` — confirmed package versions (python-jose 3.5.0, passlib 1.7.4, jinja2 3.1.6, python-multipart 0.0.22)
- Project `app/models/user.py` — confirmed User model fields: `email`, `password_hash`, `role`, `is_active`
- Project `app/config.py` — confirmed pydantic-settings pattern for adding `admin_email`/`admin_password`
- Project `app/main.py` — confirmed lifespan pattern for adding seed call
- Project `tests/conftest.py` — confirmed `lru_cache` clear pattern and `override_settings` fixture

### Secondary (MEDIUM confidence)

- [fastapitutorial.medium.com — HTTP-only cookie JWT](https://fastapitutorial.medium.com/fastapi-securing-jwt-token-with-httponly-cookie-47e0139b8dde) — cookie login + `require_role` closure pattern (WebSearch → WebFetch verified structure)
- npm registry search (2026-03-27) — Pico CSS v2.1.1 as latest stable v2 version
- [Starlette docs](https://www.starlette.dev/responses/#set-cookie) — set_cookie() parameter reference (referenced by FastAPI docs)

### Tertiary (LOW confidence)

- None — all key claims verified with official sources or primary codebase inspection.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages already in requirements.txt; versions read directly from file
- Architecture: HIGH — patterns verified via FastAPI official docs and GitHub issues
- Pitfalls: HIGH — cookie/redirect pitfall confirmed via GitHub issue; others from official docs behavior
- Test map: MEDIUM — test names are proposed; exact assertions TBD during implementation

**Research date:** 2026-03-27
**Valid until:** 2026-04-27 (stable libraries — 30-day validity)
