"""Tests for self-service password change (PWD-01)."""
import pytest
from urllib.parse import urlparse, parse_qs

from app.services.auth import verify_password


class TestPasswordChangeHappyPath:
    """Test 1-3: Successful password change flow."""

    def test_change_password_success_redirect(self, student_client, db_session):
        """POST /auth/password with valid data returns 303 redirect with success msg."""
        resp = student_client.post(
            "/auth/password",
            data={
                "current_password": "studentpass",
                "new_password": "newstudentpass",
                "confirm_password": "newstudentpass",
            },
        )
        assert resp.status_code == 303
        location = resp.headers["location"]
        assert "msg=" in location
        assert "Passwort" in location

    def test_old_password_fails_after_change(self, student_client, db_session):
        """After password change, login with old password fails."""
        # Change password
        student_client.post(
            "/auth/password",
            data={
                "current_password": "studentpass",
                "new_password": "newstudentpass",
                "confirm_password": "newstudentpass",
            },
        )
        # Logout
        student_client.post("/auth/logout")
        # Try login with old password — should fail (re-render login, status 200)
        resp = student_client.post(
            "/auth/login",
            data={"email": "student1@test.com", "password": "studentpass", "next": ""},
        )
        # Failed login re-renders login page with 200, not 303
        assert resp.status_code == 200

    def test_new_password_works_after_change(self, student_client, db_session):
        """After password change, login with new password succeeds."""
        # Change password
        student_client.post(
            "/auth/password",
            data={
                "current_password": "studentpass",
                "new_password": "newstudentpass",
                "confirm_password": "newstudentpass",
            },
        )
        # Logout
        student_client.post("/auth/logout")
        # Login with new password
        resp = student_client.post(
            "/auth/login",
            data={"email": "student1@test.com", "password": "newstudentpass", "next": ""},
        )
        assert resp.status_code == 303


class TestPasswordChangeValidation:
    """Tests 4-6: Validation error cases."""

    def test_wrong_current_password(self, student_client):
        """Wrong current password returns redirect with error containing 'aktuell'."""
        resp = student_client.post(
            "/auth/password",
            data={
                "current_password": "wrongpass",
                "new_password": "newstudentpass",
                "confirm_password": "newstudentpass",
            },
        )
        assert resp.status_code == 303
        location = resp.headers["location"]
        assert "error=" in location
        assert "aktuell" in location.lower()

    def test_mismatched_new_passwords(self, student_client):
        """Mismatched new passwords returns redirect with error containing 'stimmen nicht'."""
        resp = student_client.post(
            "/auth/password",
            data={
                "current_password": "studentpass",
                "new_password": "newstudentpass",
                "confirm_password": "differentpass",
            },
        )
        assert resp.status_code == 303
        location = resp.headers["location"]
        assert "error=" in location
        assert "stimmen+nicht" in location.lower() or "stimmen%20nicht" in location.lower()

    def test_too_short_new_password(self, student_client):
        """Password shorter than 8 chars returns redirect with error containing 'mindestens'."""
        resp = student_client.post(
            "/auth/password",
            data={
                "current_password": "studentpass",
                "new_password": "short",
                "confirm_password": "short",
            },
        )
        assert resp.status_code == 303
        location = resp.headers["location"]
        assert "error=" in location
        assert "mindestens" in location.lower()


class TestPasswordChangeAuth:
    """Test 7: Unauthenticated access."""

    def test_unauthenticated_redirects_to_login(self, test_client):
        """Unauthenticated POST to /auth/password returns 303 redirect to /login."""
        resp = test_client.post(
            "/auth/password",
            data={
                "current_password": "any",
                "new_password": "anypasswd",
                "confirm_password": "anypasswd",
            },
        )
        assert resp.status_code == 303
        assert "/login" in resp.headers["location"]


class TestPasswordChangeMultiRole:
    """Tests 8-9: Other roles can change password too."""

    def test_teacher_can_change_password(self, teacher_client, db_session):
        """Teacher can change password using same endpoint."""
        resp = teacher_client.post(
            "/auth/password",
            data={
                "current_password": "teacherpass",
                "new_password": "newteacherpass",
                "confirm_password": "newteacherpass",
            },
        )
        assert resp.status_code == 303
        location = resp.headers["location"]
        assert "/teacher" in location
        assert "msg=" in location

    def test_admin_can_change_password(self, admin_client, db_session):
        """Admin can change password using same endpoint."""
        resp = admin_client.post(
            "/auth/password",
            data={
                "current_password": "adminpass",
                "new_password": "newadminpassword",
                "confirm_password": "newadminpassword",
            },
        )
        assert resp.status_code == 303
        location = resp.headers["location"]
        assert "/admin" in location
        assert "msg=" in location
