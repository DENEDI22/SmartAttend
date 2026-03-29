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


# ── Plan 02: Lesson detail + CSV (TEACH-03, TEACH-04) ────────────────────


def test_lesson_roster_full_class(
    teacher_client, seed_schedule_entry, seed_device,
    seed_token, seed_students, seed_attendance,
):
    """Lesson detail shows full class roster with attendance status (TEACH-03)."""
    response = teacher_client.get(f"/teacher/lesson/{seed_token.id}")
    assert response.status_code == 200
    assert "Anwesenheit 10A" in response.text
    assert "R101" in response.text
    assert "Mueller" in response.text
    assert "Schmidt" in response.text
    assert "Weber" in response.text
    assert "Anwesend" in response.text
    assert "Abwesend" in response.text
    assert "2/3" in response.text


def test_lesson_access_denied_other_teacher(
    teacher_client, db_session, seed_schedule_entry, seed_device, seed_token,
):
    """Teacher cannot view another teacher's lesson (TEACH-03)."""
    from app.services.auth import get_password_hash
    from app.models.user import User

    other_teacher = User(
        email="other@test.com",
        first_name="Other",
        last_name="Teacher",
        role="teacher",
        password_hash=get_password_hash("otherpass"),
        is_active=True,
    )
    db_session.add(other_teacher)
    db_session.commit()
    db_session.refresh(other_teacher)

    seed_schedule_entry.teacher_id = other_teacher.id
    db_session.commit()
    db_session.refresh(seed_schedule_entry)

    response = teacher_client.get(f"/teacher/lesson/{seed_token.id}")
    assert response.status_code == 303
    location = response.headers.get("location", "")
    assert "error=" in location


def test_csv_export_content(
    teacher_client, seed_schedule_entry, seed_device,
    seed_token, seed_students, seed_attendance,
):
    """CSV export contains correct columns and data (TEACH-04)."""
    response = teacher_client.get(f"/teacher/lesson/{seed_token.id}/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    disposition = response.headers.get("content-disposition", "")
    assert "Anwesenheit_10A_" in disposition
    assert ".csv" in disposition

    text = response.content.decode("utf-8-sig")  # handles BOM
    assert "Nachname;Vorname;Klasse;Status;Uhrzeit" in text
    assert "Mueller;Max;10A;Anwesend" in text
    assert "Weber;Lisa;10A;Abwesend;" in text


def test_csv_encoding_and_format(
    teacher_client, seed_schedule_entry, seed_device,
    seed_token, seed_students, seed_attendance,
):
    """CSV uses UTF-8 BOM and semicolon separator (TEACH-04)."""
    response = teacher_client.get(f"/teacher/lesson/{seed_token.id}/csv")
    assert response.status_code == 200
    # Check UTF-8 BOM
    assert response.content[:3] == b"\xef\xbb\xbf"
    # Check semicolon delimiter: split a data line and verify 5 columns
    text = response.content.decode("utf-8-sig")
    lines = text.strip().split("\n")
    assert len(lines) >= 2  # header + at least 1 data row
    data_line = lines[1]
    columns = data_line.split(";")
    assert len(columns) == 5
