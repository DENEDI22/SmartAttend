"""Tests for user CSV import: template, upload, preview, confirm."""
import io
import json

from app.models.user import User
from app.services.auth import get_password_hash


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
    # Should redirect with error about missing column
    assert resp.status_code == 303
    assert "password" in resp.headers.get("location", "").lower()


def test_user_csv_confirm(admin_client, db_session):
    rows = [{"email": "new@school.de", "first_name": "Neu", "last_name": "User", "role": "student", "class_name": "10B", "password": "pass123"}]
    resp = admin_client.post("/admin/users/csv-confirm", data={"rows_json": json.dumps(rows)})
    assert resp.status_code == 303
    assert "msg=" in resp.headers["location"]
    assert "importiert" in resp.headers["location"]

    # Verify user was created
    user = db_session.query(User).filter(User.email == "new@school.de").first()
    assert user is not None
    assert user.first_name == "Neu"
    assert user.class_name == "10B"


def test_user_csv_upsert(admin_client, db_session):
    # Create user first
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

    # Upsert via CSV confirm
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
    csv_content = "email,first_name,last_name,role,class_name,password\ntest@school.de,M\u00fcller,Sch\u00f6n,student,10A,pass123"
    latin1_bytes = csv_content.encode("latin-1")
    files = {"file": ("test.csv", io.BytesIO(latin1_bytes), "text/csv")}
    resp = admin_client.post("/admin/users/csv-upload", files=files)
    assert resp.status_code == 200
    assert "M\u00fcller" in resp.text
    assert "Sch\u00f6n" in resp.text
