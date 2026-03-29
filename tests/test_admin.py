"""
Phase 3 Admin Interface tests.
Maps to ADMIN-01 through ADMIN-10.
"""
import pytest
from datetime import time
from fastapi.testclient import TestClient


# ── ADMIN-01: View devices with status ────────────────────────────
def test_devices_page_shows_devices(admin_client, db_session, seed_device):
    """GET /admin/devices shows device table with device_id, room, status (ADMIN-01)."""
    resp = admin_client.get("/admin/devices", follow_redirects=True)
    assert resp.status_code == 200
    assert "test-device-001" in resp.text
    assert "R101" in resp.text
    assert "Online" in resp.text


# ── ADMIN-02: Assign room and label ──────────────────────────────
def test_update_device_room_label(admin_client, db_session, seed_device):
    """POST /admin/devices/update changes room and label fields (ADMIN-02)."""
    resp = admin_client.post(
        "/admin/devices/update",
        data={
            f"room_{seed_device.id}": "R202",
            f"label_{seed_device.id}": "Neuer Raum",
        },
    )
    assert resp.status_code == 303
    assert "msg=" in resp.headers["location"]

    db_session.refresh(seed_device)
    assert seed_device.room == "R202"
    assert seed_device.label == "Neuer Raum"


# ── ADMIN-03: Enable/disable device ──────────────────────────────
def test_toggle_device_enabled(admin_client, db_session, seed_device):
    """POST /admin/devices/{id}/toggle flips is_enabled (ADMIN-03)."""
    assert seed_device.is_enabled is False

    resp = admin_client.post(f"/admin/devices/{seed_device.id}/toggle")
    assert resp.status_code == 303

    db_session.refresh(seed_device)
    assert seed_device.is_enabled is True

    # Toggle back
    resp = admin_client.post(f"/admin/devices/{seed_device.id}/toggle")
    db_session.refresh(seed_device)
    assert seed_device.is_enabled is False


# ── ADMIN-04: View all users ─────────────────────────────────────
def test_users_page_shows_users(admin_client, db_session):
    """GET /admin/users shows user table with name, role, class (ADMIN-04)."""
    pytest.skip("Plan 03 implements this")


# ── ADMIN-05: Create new user ────────────────────────────────────
def test_create_user(admin_client, db_session, seed_school_class):
    """POST /admin/users/create creates a new user with hashed password (ADMIN-05)."""
    pytest.skip("Plan 03 implements this")


# ── ADMIN-06: Deactivate user ────────────────────────────────────
def test_deactivate_user(admin_client, db_session):
    """POST /admin/users/{id}/deactivate sets is_active=False (ADMIN-06)."""
    pytest.skip("Plan 03 implements this")


# ── ADMIN-07: View schedule entries per device ───────────────────
def test_device_schedule_entries_shown(admin_client, db_session, seed_device, seed_teacher, seed_school_class):
    """GET /admin/devices shows schedule entries within device details (ADMIN-07)."""
    pytest.skip("Plan 04 implements this")


# ── ADMIN-08: Add schedule entry ─────────────────────────────────
def test_add_schedule_entry(admin_client, db_session, seed_device, seed_teacher, seed_school_class):
    """POST /admin/schedule/add creates a ScheduleEntry (ADMIN-08)."""
    pytest.skip("Plan 04 implements this")


# ── ADMIN-09: Reject conflicting schedule ─────────────────────────
def test_schedule_conflict_rejected(admin_client, db_session, seed_device, seed_teacher, seed_school_class):
    """POST /admin/schedule/add with overlapping time is rejected (ADMIN-09)."""
    pytest.skip("Plan 04 implements this")


# ── ADMIN-10: Delete schedule entry ──────────────────────────────
def test_delete_schedule_entry(admin_client, db_session, seed_device, seed_teacher, seed_school_class):
    """POST /admin/schedule/{id}/delete removes the entry (ADMIN-10)."""
    pytest.skip("Plan 04 implements this")


# ── Skeleton tests (verify Plan 01 infrastructure) ───────────────
def test_admin_redirect(admin_client):
    """GET /admin redirects to /admin/devices with 303."""
    resp = admin_client.get("/admin")
    assert resp.status_code == 303
    assert "/admin/devices" in resp.headers["location"]


def test_admin_devices_page_renders(admin_client):
    """GET /admin/devices returns 200 with nav bar."""
    resp = admin_client.get("/admin/devices", follow_redirects=True)
    assert resp.status_code == 200
    assert "Geräte" in resp.text or "Ger" in resp.text
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


def test_admin_requires_admin_role(test_client, db_session, seed_teacher):
    """GET /admin/devices with teacher role returns 403."""
    resp = test_client.post(
        "/auth/login",
        data={"email": "teacher@test.com", "password": "teacherpass", "next": ""},
    )
    assert resp.status_code == 303
    resp = test_client.get("/admin/devices")
    assert resp.status_code == 403
