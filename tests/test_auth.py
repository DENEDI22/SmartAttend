"""
Phase 2 Authentication tests.
Maps to VALIDATION.md task IDs 02-01-xx through 02-03-xx.
"""
import pytest
from datetime import datetime, timedelta, timezone

from app.models.user import User
from app.services.auth import create_access_token, get_password_hash, ALGORITHM
from app.config import get_settings


# ── Helper ──────────────────────────────────────────────────────────────────

def make_user(db, email="test@example.com", password="secret", role="admin", is_active=True):
    """Create and persist a test user. Returns the User ORM object."""
    user = User(
        email=email,
        first_name="Test",
        last_name="User",
        role=role,
        password_hash=get_password_hash(password),
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(client, email="test@example.com", password="secret", next_url=""):
    """Helper: POST /auth/login and return the response."""
    return client.post(
        "/auth/login",
        data={"email": email, "password": password, "next": next_url},
    )


def get_auth_cookie(client, db, role="admin"):
    """Create a user, log in, return the access_token cookie value."""
    user = make_user(db, email=f"{role}@example.com", role=role)
    resp = login(client, email=user.email)
    assert resp.status_code == 303, f"Login failed: {resp.status_code}"
    return resp.cookies.get("access_token")


# ── Plan 01: Login page (AUTH-07) ──────────────────────────────────────────

def test_login_page_renders(test_client):
    """GET /login returns 200 and contains the login form (AUTH-07)."""
    response = test_client.get("/login")
    assert response.status_code == 200
    assert 'name="email"' in response.text
    assert 'name="password"' in response.text
    assert "Anmelden" in response.text


def test_login_page_next_param(test_client):
    """GET /login?next=/checkin?token=abc threads next into hidden input (AUTH-07)."""
    response = test_client.get("/login", params={"next": "/checkin?token=abc"})
    assert response.status_code == 200
    assert 'value="/checkin?token=abc"' in response.text


# ── Plan 01: Login POST (AUTH-01) ──────────────────────────────────────────

def test_login_success(test_client, db_session):
    """POST /auth/login with valid credentials returns 303 redirect (AUTH-01)."""
    make_user(db_session)
    response = login(test_client)
    assert response.status_code == 303
    assert "access_token" in response.cookies


def test_login_invalid_credentials(test_client, db_session):
    """POST /auth/login with wrong password re-renders login with German error (AUTH-01)."""
    make_user(db_session)
    response = login(test_client, password="wrongpassword")
    assert response.status_code == 200
    assert "Ungültige E-Mail oder Passwort." in response.text


def test_login_inactive_user(test_client, db_session):
    """POST /auth/login with is_active=False renders 'Dieses Konto ist deaktiviert.' (AUTH-01)."""
    make_user(db_session, is_active=False)
    response = login(test_client)
    assert response.status_code == 200
    assert "Dieses Konto ist deaktiviert." in response.text


# ── Plan 02: Cookie (AUTH-02, AUTH-03) + Logout (AUTH-04) + /me (AUTH-05) ──

def test_login_cookie_httponly(test_client, db_session):
    """Successful login sets access_token cookie with HttpOnly flag (AUTH-02)."""
    make_user(db_session)
    response = login(test_client)
    assert response.status_code == 303
    set_cookie_header = response.headers.get("set-cookie", "")
    assert "HttpOnly" in set_cookie_header


def test_token_expiry_admin(db_session):
    """Admin token expires in 8 hours — JWT exp claim is within 10s of now+8h (AUTH-03)."""
    from jose import jwt
    token = create_access_token(
        data={"sub": "1", "role": "admin"},
        expires_delta=timedelta(hours=8),
    )
    payload = jwt.decode(token, get_settings().secret_key, algorithms=[ALGORITHM])
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    expected = datetime.now(timezone.utc) + timedelta(hours=8)
    assert abs((exp - expected).total_seconds()) < 10


def test_token_expiry_student(db_session):
    """Student token expires in 1 hour — JWT exp claim is within 10s of now+1h (AUTH-03)."""
    from jose import jwt
    token = create_access_token(
        data={"sub": "1", "role": "student"},
        expires_delta=timedelta(hours=1),
    )
    payload = jwt.decode(token, get_settings().secret_key, algorithms=[ALGORITHM])
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    expected = datetime.now(timezone.utc) + timedelta(hours=1)
    assert abs((exp - expected).total_seconds()) < 10


def test_logout(test_client, db_session):
    """POST /auth/logout clears access_token cookie and redirects to /login (AUTH-04)."""
    make_user(db_session)
    login(test_client)  # sets the cookie in the client's cookie jar
    response = test_client.post("/auth/logout")
    assert response.status_code == 303
    assert response.headers["location"] == "/login"
    # Cookie should be deleted (max-age=0 or set-cookie clears it)
    set_cookie = response.headers.get("set-cookie", "")
    assert "access_token" in set_cookie


def test_me_authenticated(test_client, db_session):
    """GET /auth/me returns user JSON for authenticated user (AUTH-05)."""
    user = make_user(db_session)
    login_resp = login(test_client)
    assert login_resp.status_code == 303
    token = login_resp.cookies.get("access_token")
    response = test_client.get("/auth/me", cookies={"access_token": token})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user.email
    assert data["role"] == user.role
    assert "id" in data
    assert "first_name" in data
    assert "last_name" in data


def test_me_unauthenticated(test_client):
    """GET /auth/me with no cookie redirects to /login (AUTH-05, D-07)."""
    response = test_client.get("/auth/me")
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


# ── Plan 03: Role enforcement (AUTH-06) ────────────────────────────────────

def test_require_role_wrong_role(test_client, db_session):
    """Student accessing admin-only route returns 403 (AUTH-06)."""
    make_user(db_session, email="student@example.com", role="student")
    login_resp = login(test_client, email="student@example.com")
    assert login_resp.status_code == 303
    token = login_resp.cookies.get("access_token")
    response = test_client.get("/auth/admin-only-test", cookies={"access_token": token})
    assert response.status_code == 403


def test_require_role_correct_role(test_client, db_session):
    """Admin accessing admin-only route returns 200 (AUTH-06)."""
    make_user(db_session, email="admin@example.com", role="admin")
    login_resp = login(test_client, email="admin@example.com")
    assert login_resp.status_code == 303
    token = login_resp.cookies.get("access_token")
    response = test_client.get("/auth/admin-only-test", cookies={"access_token": token})
    assert response.status_code == 200
