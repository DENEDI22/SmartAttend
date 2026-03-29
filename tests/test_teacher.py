"""
Phase 4 Teacher Interface tests.
Plan 01: Dashboard (TEACH-01, TEACH-02)
Plan 02 stubs: Lesson detail + CSV (TEACH-03, TEACH-04)
"""
import pytest


# ── Plan 01: Dashboard (TEACH-01, TEACH-02) ───────────────────────────────


def test_dashboard_shows_todays_lessons(teacher_client, seed_schedule_entry, seed_device):
    """GET /teacher shows today's lessons with class name and room (TEACH-01)."""
    response = teacher_client.get("/teacher")
    assert response.status_code == 200
    assert "Meine Stunden heute" in response.text
    assert seed_schedule_entry.class_name in response.text  # "10A"
    assert seed_device.room in response.text  # "R101"


def test_dashboard_empty_state(teacher_client):
    """GET /teacher with no schedule entries shows empty state (TEACH-01)."""
    response = teacher_client.get("/teacher")
    assert response.status_code == 200
    assert "Heute keine Stunden geplant" in response.text


def test_dashboard_shows_attendance_count(
    teacher_client, seed_schedule_entry, seed_device,
    seed_token, seed_students, seed_attendance,
):
    """GET /teacher shows checked-in/expected count (TEACH-02)."""
    response = teacher_client.get("/teacher")
    assert response.status_code == 200
    assert "2/3" in response.text


def test_dashboard_no_token_shows_dash(
    teacher_client, seed_schedule_entry, seed_device, seed_students,
):
    """GET /teacher with no token shows '--' and no Details link (TEACH-02)."""
    response = teacher_client.get("/teacher")
    assert response.status_code == 200
    assert "--" in response.text
    assert "Details" not in response.text


def test_teacher_requires_auth(test_client):
    """GET /teacher without auth redirects to login (303)."""
    response = test_client.get("/teacher")
    assert response.status_code == 303
    assert "/login" in response.headers.get("location", "")


# ── Plan 02 stubs: Lesson detail + CSV (TEACH-03, TEACH-04) ───────────────


@pytest.mark.skip(reason="Plan 02")
def test_lesson_roster_full_class():
    """Lesson detail shows full class roster with attendance status (TEACH-03)."""
    pass


@pytest.mark.skip(reason="Plan 02")
def test_lesson_access_denied_other_teacher():
    """Teacher cannot view another teacher's lesson (TEACH-03)."""
    pass


@pytest.mark.skip(reason="Plan 02")
def test_csv_export_content():
    """CSV export contains correct columns and data (TEACH-04)."""
    pass


@pytest.mark.skip(reason="Plan 02")
def test_csv_encoding_and_format():
    """CSV uses UTF-8 BOM and semicolon separator (TEACH-04)."""
    pass
