"""Tests for student check-in flow (CHKIN-01 through CHKIN-07)."""
import uuid
from datetime import date, datetime, timedelta

from app.models.attendance_record import AttendanceRecord
from app.models.attendance_token import AttendanceToken


def test_checkin_page_shows_lesson_info(student_client, seed_token):
    """CHKIN-01: GET /checkin?token=... returns 200 with room and time info."""
    resp = student_client.get(f"/checkin?token={seed_token.token}")
    assert resp.status_code == 200
    assert "R101" in resp.text
    assert "08:00" in resp.text
    assert "09:30" in resp.text


def test_checkin_unauthenticated_redirects_to_login(test_client, seed_token):
    """CHKIN-02: GET /checkin?token=... without auth redirects to /login."""
    resp = test_client.get(f"/checkin?token={seed_token.token}")
    assert resp.status_code == 303
    assert "/login" in resp.headers["location"]
    assert seed_token.token in resp.headers["location"]


def test_checkin_post_validates_token(student_client, seed_token):
    """CHKIN-03: POST /checkin with valid token returns 200 success page."""
    resp = student_client.post("/checkin", data={"token": seed_token.token})
    assert resp.status_code == 200
    assert "erfolgreich" in resp.text


def test_checkin_duplicate_rejected(student_client, seed_token, db_session):
    """CHKIN-04: POST /checkin twice with same token, second shows already checked in."""
    student_client.post("/checkin", data={"token": seed_token.token})
    resp = student_client.post("/checkin", data={"token": seed_token.token})
    assert resp.status_code == 200
    assert "bereits" in resp.text.lower() or "Eingecheckt um" in resp.text


def test_checkin_success_writes_record(student_client, seed_token, db_session, seed_students):
    """CHKIN-05: POST /checkin with valid token creates an AttendanceRecord row."""
    student_client.post("/checkin", data={"token": seed_token.token})
    record = db_session.query(AttendanceRecord).filter(
        AttendanceRecord.token_id == seed_token.id,
        AttendanceRecord.student_id == seed_students[0].id,
    ).first()
    assert record is not None
    assert record.checked_in_at is not None


def test_checkin_expired_token_error(student_client, db_session, seed_schedule_entry):
    """CHKIN-06: Expired token shows 'Diese Stunde ist bereits beendet'."""
    expired_token = AttendanceToken(
        token=str(uuid.uuid4()),
        device_id=seed_schedule_entry.device_id,
        schedule_entry_id=seed_schedule_entry.id,
        lesson_date=date.today(),
        is_active=True,
        created_at=datetime.now() - timedelta(hours=3),
        expires_at=datetime.now() - timedelta(hours=1),
    )
    db_session.add(expired_token)
    db_session.commit()
    db_session.refresh(expired_token)
    resp = student_client.get(f"/checkin?token={expired_token.token}")
    assert resp.status_code == 200
    assert "Diese Stunde ist bereits beendet" in resp.text


def test_checkin_invalid_token_error(student_client):
    """CHKIN-07: GET /checkin?token=nonexistent-uuid shows error."""
    resp = student_client.get("/checkin?token=00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 200
    assert "fehlender Token" in resp.text


def test_checkin_missing_token_error(student_client):
    """CHKIN-07: GET /checkin (no token param) shows error."""
    resp = student_client.get("/checkin")
    assert resp.status_code == 200
    assert "fehlender Token" in resp.text


def test_checkin_inactive_token_error(student_client, seed_token, db_session):
    """D-11: Inactive token shows 'Dieser Token ist nicht mehr gueltig'."""
    seed_token.is_active = False
    db_session.commit()
    db_session.refresh(seed_token)
    resp = student_client.get(f"/checkin?token={seed_token.token}")
    assert resp.status_code == 200
    assert "nicht mehr" in resp.text


def test_checkin_non_student_rejected(teacher_client, seed_token):
    """D-05: Teacher accessing check-in sees role restriction error."""
    resp = teacher_client.get(f"/checkin?token={seed_token.token}")
    assert resp.status_code == 200
    assert "Nur Sch" in resp.text


def test_checkin_already_checked_in_shows_time(student_client, seed_token, db_session):
    """D-03: After check-in, GET shows 'Eingecheckt um' with time."""
    student_client.post("/checkin", data={"token": seed_token.token})
    resp = student_client.get(f"/checkin?token={seed_token.token}")
    assert resp.status_code == 200
    assert "Eingecheckt um" in resp.text
