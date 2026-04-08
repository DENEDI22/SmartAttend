"""Tests for CSV import: users (Plan 14-01) and schedules (Plan 14-02)."""
import io
import json
from datetime import time

import pytest

from app.models.device import Device
from app.models.schedule_entry import ScheduleEntry
from app.models.user import User
from app.services.auth import get_password_hash


# ── User CSV Tests ───────────────────────────────────────────────────


def make_csv_upload(content: str, filename: str = "test.csv"):
    return {"file": (filename, io.BytesIO(content.encode("utf-8")), "text/csv")}


def test_user_template_download(admin_client):
    resp = admin_client.get("/admin/users/csv-template")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "email,first_name,last_name,role,class_name,password" in resp.text
    assert "max.mustermann@schule.de" in resp.text


def test_user_csv_preview_valid(admin_client):
    csv_content = "email,first_name,last_name,role,class_name,password\ntest@school.de,Max,Muster,student,10A,pass123"
    resp = admin_client.post("/admin/users/csv-upload", files=make_csv_upload(csv_content))
    assert resp.status_code == 200
    assert "Vorschau" in resp.text
    assert "OK" in resp.text
    assert "Import bestaetigen" in resp.text


def test_user_csv_preview_invalid_role(admin_client):
    csv_content = "email,first_name,last_name,role,class_name,password\ntest@school.de,Max,Muster,invalid,10A,pass123"
    resp = admin_client.post("/admin/users/csv-upload", files=make_csv_upload(csv_content))
    assert resp.status_code == 200
    assert "Ungueltige Rolle" in resp.text


def test_user_csv_preview_missing_field(admin_client):
    csv_content = "email,first_name,last_name,role,class_name\ntest@school.de,Max,Muster,student,10A"
    resp = admin_client.post("/admin/users/csv-upload", files=make_csv_upload(csv_content))
    assert resp.status_code == 303
    assert "password" in resp.headers.get("location", "").lower()


def test_user_csv_confirm(admin_client, db_session):
    rows = [{"email": "new@school.de", "first_name": "Neu", "last_name": "User", "role": "student", "class_name": "10B", "password": "pass123"}]
    resp = admin_client.post("/admin/users/csv-confirm", data={"rows_json": json.dumps(rows)})
    assert resp.status_code == 303
    assert "msg=" in resp.headers["location"]
    assert "importiert" in resp.headers["location"]

    user = db_session.query(User).filter(User.email == "new@school.de").first()
    assert user is not None
    assert user.first_name == "Neu"
    assert user.class_name == "10B"


def test_user_csv_upsert(admin_client, db_session):
    existing = User(
        email="existing@school.de",
        first_name="Old",
        last_name="Name",
        role="student",
        password_hash=get_password_hash("oldpass"),
        is_active=True,
    )
    db_session.add(existing)
    db_session.commit()

    rows = [{"email": "existing@school.de", "first_name": "Updated", "last_name": "Name", "role": "teacher", "class_name": "", "password": "newpass123"}]
    resp = admin_client.post("/admin/users/csv-confirm", data={"rows_json": json.dumps(rows)})
    assert resp.status_code == 303

    db_session.refresh(existing)
    assert existing.first_name == "Updated"
    assert existing.role == "teacher"


def test_user_csv_empty(admin_client):
    csv_content = "email,first_name,last_name,role,class_name,password\n"
    resp = admin_client.post("/admin/users/csv-upload", files=make_csv_upload(csv_content))
    assert resp.status_code == 303
    assert "Keine+Datenzeilen" in resp.headers["location"]


def test_user_csv_file_too_large(admin_client):
    csv_content = "email,first_name,last_name,role,class_name,password\n" + "x" * 1_048_577
    resp = admin_client.post("/admin/users/csv-upload", files=make_csv_upload(csv_content))
    assert resp.status_code == 303
    assert "gross" in resp.headers["location"]


def test_user_csv_encoding_latin1(admin_client):
    csv_content = "email,first_name,last_name,role,class_name,password\ntest@school.de,Müller,Schön,student,10A,pass123"
    latin1_bytes = csv_content.encode("latin-1")
    files = {"file": ("test.csv", io.BytesIO(latin1_bytes), "text/csv")}
    resp = admin_client.post("/admin/users/csv-upload", files=files)
    assert resp.status_code == 200
    assert "Müller" in resp.text
    assert "Schön" in resp.text


# ── Schedule CSV Tests ────────────────────────────────────────────────


def test_schedule_template_download(admin_client):
    """GET /admin/schedule/csv-template returns CSV with correct headers."""
    resp = admin_client.get("/admin/schedule/csv-template")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "device_id,teacher_email,class_name,weekday,start_time,end_time,late_threshold_minutes" in resp.text


def test_schedule_csv_preview_valid(admin_client, db_session, seed_device, seed_teacher):
    """Upload valid schedule CSV shows preview with OK status."""
    csv_content = (
        "device_id,teacher_email,class_name,weekday,start_time,end_time,late_threshold_minutes\n"
        f"{seed_device.device_id},{seed_teacher.email},10A,1,08:00,09:30,\n"
    )
    resp = admin_client.post(
        "/admin/schedule/csv-upload",
        files={"file": ("schedule.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    assert resp.status_code == 200
    assert "Vorschau" in resp.text
    assert "OK" in resp.text
    assert "Import bestaetigen" in resp.text


def test_schedule_csv_preview_bad_device(admin_client, db_session, seed_teacher):
    """Upload CSV with nonexistent device shows error."""
    csv_content = (
        "device_id,teacher_email,class_name,weekday,start_time,end_time,late_threshold_minutes\n"
        f"zzz999,{seed_teacher.email},10A,1,08:00,09:30,\n"
    )
    resp = admin_client.post(
        "/admin/schedule/csv-upload",
        files={"file": ("schedule.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    assert resp.status_code == 200
    assert "Geraet" in resp.text and "zzz999" in resp.text and "nicht gefunden" in resp.text


def test_schedule_csv_preview_bad_teacher(admin_client, db_session, seed_device):
    """Upload CSV with nonexistent teacher email shows error."""
    csv_content = (
        "device_id,teacher_email,class_name,weekday,start_time,end_time,late_threshold_minutes\n"
        f"{seed_device.device_id},nobody@test.com,10A,1,08:00,09:30,\n"
    )
    resp = admin_client.post(
        "/admin/schedule/csv-upload",
        files={"file": ("schedule.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    assert resp.status_code == 200
    assert "nicht gefunden" in resp.text


def test_schedule_csv_preview_overlap_db(admin_client, db_session, seed_device, seed_teacher):
    """Upload CSV overlapping with existing DB entry shows error."""
    entry = ScheduleEntry(
        device_id=seed_device.id,
        teacher_id=seed_teacher.id,
        class_name="9B",
        weekday=1,
        start_time=time(8, 0),
        end_time=time(9, 30),
    )
    db_session.add(entry)
    db_session.commit()

    csv_content = (
        "device_id,teacher_email,class_name,weekday,start_time,end_time,late_threshold_minutes\n"
        f"{seed_device.device_id},{seed_teacher.email},10A,1,08:30,09:00,\n"
    )
    resp = admin_client.post(
        "/admin/schedule/csv-upload",
        files={"file": ("schedule.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    assert resp.status_code == 200
    assert "Ueberschneidung mit bestehendem Eintrag" in resp.text


def test_schedule_csv_preview_overlap_intra(admin_client, db_session, seed_device, seed_teacher):
    """Upload CSV with two rows overlapping each other shows intra-CSV error."""
    csv_content = (
        "device_id,teacher_email,class_name,weekday,start_time,end_time,late_threshold_minutes\n"
        f"{seed_device.device_id},{seed_teacher.email},10A,1,08:00,09:30,\n"
        f"{seed_device.device_id},{seed_teacher.email},10B,1,09:00,10:00,\n"
    )
    resp = admin_client.post(
        "/admin/schedule/csv-upload",
        files={"file": ("schedule.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    assert resp.status_code == 200
    assert "Ueberschneidung mit Zeile" in resp.text


def test_schedule_csv_confirm(admin_client, db_session, seed_device, seed_teacher):
    """Confirm valid rows creates ScheduleEntry in DB."""
    rows_json = json.dumps([{
        "device_id": seed_device.device_id,
        "teacher_email": seed_teacher.email,
        "class_name": "10A",
        "weekday": "2",
        "start_time": "10:00",
        "end_time": "11:30",
        "late_threshold_minutes": "",
    }])
    resp = admin_client.post(
        "/admin/schedule/csv-confirm",
        data={"rows_json": rows_json},
    )
    assert resp.status_code == 303
    assert "msg=" in resp.headers["location"]
    assert "Stundenplaneintraege" in resp.headers["location"]

    entry = db_session.query(ScheduleEntry).filter(
        ScheduleEntry.device_id == seed_device.id,
        ScheduleEntry.class_name == "10A",
    ).first()
    assert entry is not None
    assert entry.weekday == 2
    assert entry.start_time == time(10, 0)
    assert entry.end_time == time(11, 30)


def test_schedule_csv_invalid_time(admin_client, db_session, seed_device, seed_teacher):
    """Upload CSV with invalid time format shows error."""
    csv_content = (
        "device_id,teacher_email,class_name,weekday,start_time,end_time,late_threshold_minutes\n"
        f"{seed_device.device_id},{seed_teacher.email},10A,1,25:00,09:30,\n"
    )
    resp = admin_client.post(
        "/admin/schedule/csv-upload",
        files={"file": ("schedule.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    assert resp.status_code == 200
    assert "Ungueltiges Zeitformat" in resp.text


def test_schedule_csv_start_after_end(admin_client, db_session, seed_device, seed_teacher):
    """Upload CSV with start_time after end_time shows error."""
    csv_content = (
        "device_id,teacher_email,class_name,weekday,start_time,end_time,late_threshold_minutes\n"
        f"{seed_device.device_id},{seed_teacher.email},10A,1,10:00,09:00,\n"
    )
    resp = admin_client.post(
        "/admin/schedule/csv-upload",
        files={"file": ("schedule.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    assert resp.status_code == 200
    assert "Startzeit muss vor Endzeit liegen" in resp.text
