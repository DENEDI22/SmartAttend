"""
Phase 3 Admin Interface tests.
Maps to ADMIN-01 through ADMIN-10.
"""
import pytest
from datetime import time


# -- ADMIN-01: View devices with status ----------------------------------------
def test_devices_page_shows_devices(admin_client, db_session, seed_device):
    """GET /admin/devices shows device table with device_id, room, status (ADMIN-01)."""
    pytest.skip("Plan 02 implements this")


# -- ADMIN-02: Assign room and label ------------------------------------------
def test_update_device_room_label(admin_client, db_session, seed_device):
    """POST /admin/devices/update changes room and label fields (ADMIN-02)."""
    pytest.skip("Plan 02 implements this")


# -- ADMIN-03: Enable/disable device ------------------------------------------
def test_toggle_device_enabled(admin_client, db_session, seed_device):
    """POST /admin/devices/{id}/toggle flips is_enabled (ADMIN-03)."""
    pytest.skip("Plan 02 implements this")


# -- ADMIN-04: View all users -------------------------------------------------
def test_users_page_shows_users(admin_client, db_session):
    """GET /admin/users shows user table with name, role, class (ADMIN-04)."""
    # admin_client already created an admin user during login
    resp = admin_client.get("/admin/users", follow_redirects=True)
    assert resp.status_code == 200
    assert "Admin" in resp.text
    assert "admin@test.com" in resp.text
    assert "Aktiv" in resp.text


# -- ADMIN-05: Create new user ------------------------------------------------
def test_create_user(admin_client, db_session, seed_school_class):
    """POST /admin/users/create creates a new user with hashed password (ADMIN-05)."""
    resp = admin_client.post(
        "/admin/users/create",
        data={
            "first_name": "Max",
            "last_name": "Mustermann",
            "email": "max@test.com",
            "password": "securepass123",
            "role": "student",
            "class_name": "10A",
        },
    )
    assert resp.status_code == 303
    assert "msg=" in resp.headers["location"]

    from app.models.user import User
    new_user = db_session.query(User).filter(User.email == "max@test.com").first()
    assert new_user is not None
    assert new_user.first_name == "Max"
    assert new_user.last_name == "Mustermann"
    assert new_user.role == "student"
    assert new_user.class_name == "10A"
    assert new_user.is_active is True
    assert new_user.password_hash != "securepass123"  # hashed, not plain


# -- ADMIN-06: Deactivate user ------------------------------------------------
def test_deactivate_user(admin_client, db_session):
    """POST /admin/users/{id}/deactivate sets is_active=False (ADMIN-06)."""
    from app.models.user import User
    from app.services.auth import get_password_hash

    target = User(
        email="deactivate-me@test.com",
        first_name="Delete",
        last_name="Me",
        role="student",
        password_hash=get_password_hash("pass"),
        is_active=True,
    )
    db_session.add(target)
    db_session.commit()
    db_session.refresh(target)

    resp = admin_client.post(f"/admin/users/{target.id}/deactivate")
    assert resp.status_code == 303

    db_session.refresh(target)
    assert target.is_active is False

    # User still visible in list (soft delete, per D-10)
    resp = admin_client.get("/admin/users", follow_redirects=True)
    assert "deactivate-me@test.com" in resp.text
    assert "Inaktiv" in resp.text


# -- ADMIN-05 edge case: duplicate email --------------------------------------
def test_create_user_duplicate_email(admin_client, db_session):
    """POST /admin/users/create with duplicate email shows error (ADMIN-05 edge case)."""
    # admin@test.com already exists from admin_client fixture
    resp = admin_client.post(
        "/admin/users/create",
        data={
            "first_name": "Dup",
            "last_name": "User",
            "email": "admin@test.com",
            "password": "password123",
            "role": "student",
            "class_name": "",
        },
    )
    assert resp.status_code == 303
    assert "error=" in resp.headers["location"]


# -- D-14: auto-create SchoolClass --------------------------------------------
def test_create_user_auto_creates_school_class(admin_client, db_session):
    """POST /admin/users/create with new class_name auto-creates SchoolClass (D-14)."""
    resp = admin_client.post(
        "/admin/users/create",
        data={
            "first_name": "New",
            "last_name": "Class",
            "email": "newclass@test.com",
            "password": "password123",
            "role": "student",
            "class_name": "11B",
        },
    )
    assert resp.status_code == 303

    from app.models.school_class import SchoolClass
    sc = db_session.query(SchoolClass).filter(SchoolClass.name == "11B").first()
    assert sc is not None


# -- ADMIN-07: View schedule entries per device --------------------------------
def test_device_schedule_entries_shown(admin_client, db_session, seed_device, seed_teacher, seed_school_class):
    """GET /admin/devices shows schedule entries within device details (ADMIN-07)."""
    pytest.skip("Plan 04 implements this")


# -- ADMIN-08: Add schedule entry ----------------------------------------------
def test_add_schedule_entry(admin_client, db_session, seed_device, seed_teacher, seed_school_class):
    """POST /admin/schedule/add creates a ScheduleEntry (ADMIN-08)."""
    pytest.skip("Plan 04 implements this")


# -- ADMIN-09: Reject conflicting schedule -------------------------------------
def test_schedule_conflict_rejected(admin_client, db_session, seed_device, seed_teacher, seed_school_class):
    """POST /admin/schedule/add with overlapping time is rejected (ADMIN-09)."""
    pytest.skip("Plan 04 implements this")


# -- ADMIN-10: Delete schedule entry -------------------------------------------
def test_delete_schedule_entry(admin_client, db_session, seed_device, seed_teacher, seed_school_class):
    """POST /admin/schedule/{id}/delete removes the entry (ADMIN-10)."""
    pytest.skip("Plan 04 implements this")


# -- Skeleton tests (verify Plan 01 infrastructure) ----------------------------
def test_admin_redirect(admin_client):
    """GET /admin redirects to /admin/devices with 303."""
    resp = admin_client.get("/admin")
    assert resp.status_code == 303
    assert "/admin/devices" in resp.headers["location"]


def test_admin_devices_page_renders(admin_client):
    """GET /admin/devices returns 200 with nav bar."""
    resp = admin_client.get("/admin/devices", follow_redirects=True)
    assert resp.status_code == 200
    assert "Benutzer" in resp.text


def test_admin_users_page_renders(admin_client):
    """GET /admin/users returns 200 with nav bar."""
    resp = admin_client.get("/admin/users", follow_redirects=True)
    assert resp.status_code == 200
    assert "Benutzerverwaltung" in resp.text


def test_admin_requires_auth(test_client):
    """GET /admin/devices without auth redirects to /login."""
    resp = test_client.get("/admin/devices")
    assert resp.status_code == 303
    assert "/login" in resp.headers["location"]


def test_admin_requires_admin_role(test_client, db_session):
    """GET /admin/devices with teacher role returns 403."""
    from app.services.auth import get_password_hash
    from app.models.user import User

    teacher = User(
        email="teacher-nonadmin@test.com",
        first_name="T",
        last_name="T",
        role="teacher",
        password_hash=get_password_hash("pass"),
        is_active=True,
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    resp = test_client.post(
        "/auth/login",
        data={"email": "teacher-nonadmin@test.com", "password": "pass", "next": ""},
    )
    assert resp.status_code == 303
    resp = test_client.get("/admin/devices")
    assert resp.status_code == 403
