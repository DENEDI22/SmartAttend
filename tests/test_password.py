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


# ── Admin Password Reset Tests (PWD-02) ──────────────────────────────────


class TestAdminResetHappyPath:
    """Tests 1-3: Admin resets another user's password."""

    def _create_target(self, db_session):
        target = User(
            email="target@test.com",
            first_name="Target",
            last_name="User",
            role="student",
            password_hash=get_password_hash("oldpassword"),
            is_active=True,
        )
        db_session.add(target)
        db_session.commit()
        db_session.refresh(target)
        return target

    def test_admin_reset_sets_new_hash(self, admin_client, db_session):
        """POST /admin/users/{id}/reset-password with new_password sets new password hash."""
        target = self._create_target(db_session)
        resp = admin_client.post(
            f"/admin/users/{target.id}/reset-password",
            data={"new_password": "NewPass123"},
        )
        assert resp.status_code == 303
        location = resp.headers["location"]
        assert "msg=" in location
        assert "zurueckgesetzt" in location.lower()
        # Verify hash was updated
        db_session.refresh(target)
        assert verify_password("NewPass123", target.password_hash)

    def test_admin_reset_user_can_login_with_new_password(self, admin_client, db_session):
        """After reset, user can log in with new password."""
        target = self._create_target(db_session)
        admin_client.post(
            f"/admin/users/{target.id}/reset-password",
            data={"new_password": "NewPass123"},
        )
        # Logout admin
        admin_client.post("/auth/logout")
        # Login as target with new password
        resp = admin_client.post(
            "/auth/login",
            data={"email": "target@test.com", "password": "NewPass123", "next": ""},
        )
        assert resp.status_code == 303

    def test_admin_reset_old_password_fails(self, admin_client, db_session):
        """After reset, user cannot log in with old password."""
        target = self._create_target(db_session)
        admin_client.post(
            f"/admin/users/{target.id}/reset-password",
            data={"new_password": "NewPass123"},
        )
        # Logout admin
        admin_client.post("/auth/logout")
        # Login as target with OLD password — should fail
        resp = admin_client.post(
            "/auth/login",
            data={"email": "target@test.com", "password": "oldpassword", "next": ""},
        )
        assert resp.status_code == 200  # Failed login re-renders login page


class TestAdminResetValidation:
    """Tests 4-5: Validation error cases."""

    def test_admin_reset_too_short_password(self, admin_client, db_session):
        """Password shorter than 8 chars returns redirect with error containing 'mindestens'."""
        target = User(
            email="target2@test.com",
            first_name="Target",
            last_name="Two",
            role="student",
            password_hash=get_password_hash("oldpassword"),
            is_active=True,
        )
        db_session.add(target)
        db_session.commit()
        db_session.refresh(target)

        resp = admin_client.post(
            f"/admin/users/{target.id}/reset-password",
            data={"new_password": "short"},
        )
        assert resp.status_code == 303
        location = resp.headers["location"]
        assert "error=" in location
        assert "mindestens" in location.lower()

    def test_admin_reset_nonexistent_user(self, admin_client, db_session):
        """POST for non-existent user_id returns redirect with error containing 'nicht gefunden'."""
        resp = admin_client.post(
            "/admin/users/99999/reset-password",
            data={"new_password": "NewPass123"},
        )
        assert resp.status_code == 303
        location = resp.headers["location"]
        assert "error=" in location
        assert "nicht+gefunden" in location.lower() or "nicht%20gefunden" in location.lower()


class TestAdminResetAuth:
    """Tests 6-7: Authorization and authentication."""

    def test_teacher_cannot_reset_password(self, teacher_client, db_session):
        """Non-admin (teacher) cannot access endpoint (403)."""
        target = User(
            email="target3@test.com",
            first_name="Target",
            last_name="Three",
            role="student",
            password_hash=get_password_hash("oldpassword"),
            is_active=True,
        )
        db_session.add(target)
        db_session.commit()
        db_session.refresh(target)

        resp = teacher_client.post(
            f"/admin/users/{target.id}/reset-password",
            data={"new_password": "NewPass123"},
        )
        assert resp.status_code == 403

    def test_unauthenticated_reset_redirects_to_login(self, test_client):
        """Unauthenticated request redirects to /login (303)."""
        resp = test_client.post(
            "/admin/users/1/reset-password",
            data={"new_password": "NewPass123"},
        )
        assert resp.status_code == 303
        assert "/login" in resp.headers["location"]
