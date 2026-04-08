"""Tests for schedule CSV import (Plan 14-02)."""
import io
import json
from datetime import time

import pytest

from app.models.device import Device
from app.models.schedule_entry import ScheduleEntry
from app.models.user import User
from app.services.auth import get_password_hash


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
    # Create existing schedule entry
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

    # Verify DB entry
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
