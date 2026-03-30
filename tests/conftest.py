import os
import uuid
import pytest
from datetime import date, datetime, time, timedelta

import app.database as _app_database
import app.main as _app_main
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.device import Device
from app.models.schedule_entry import ScheduleEntry
from app.models.attendance_token import AttendanceToken
from app.models.attendance_record import AttendanceRecord
from app.services.auth import get_password_hash

# Override DATABASE_URL so tests never touch the real database file
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(autouse=True)
def override_settings(monkeypatch):
    """Override env vars so pydantic-settings does not need a .env file during tests."""
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-pytest-only")
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("MQTT_BROKER", "localhost")
    monkeypatch.setenv("MQTT_PORT", "1883")
    monkeypatch.setenv("SERVER_IP", "127.0.0.1")
    monkeypatch.setenv("ADMIN_EMAIL", "")
    monkeypatch.setenv("ADMIN_PASSWORD", "")
    # Clear lru_cache so each test gets fresh settings
    from app.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def db_session(override_settings, monkeypatch):
    """In-memory SQLite session with all tables created. Depends on override_settings."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Patch the module-level engine so the lifespan create_all uses in-memory DB
    monkeypatch.setattr(_app_database, "engine", test_engine)
    monkeypatch.setattr(_app_main, "engine", test_engine)
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def test_client(db_session):
    """TestClient with get_db overridden to use the in-memory db_session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, follow_redirects=False) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client(test_client, db_session):
    """TestClient pre-authenticated as admin. Creates admin user and logs in."""
    admin = User(
        email="admin@test.com",
        first_name="Admin",
        last_name="Test",
        role="admin",
        password_hash=get_password_hash("adminpass"),
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    resp = test_client.post(
        "/auth/login",
        data={"email": "admin@test.com", "password": "adminpass", "next": ""},
    )
    assert resp.status_code == 303
    # Cookie is now set on test_client
    return test_client


# ── Seed fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def seed_device(db_session):
    """Seed a Device for test use."""
    device = Device(
        device_id="test-device-001",
        room="R101",
        label="Test Device",
        is_enabled=True,
        is_online=True,
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


@pytest.fixture
def seed_teacher(db_session):
    """Seed a teacher user."""
    teacher = User(
        email="teacher@test.com",
        first_name="Lehrer",
        last_name="Test",
        role="teacher",
        password_hash=get_password_hash("teacherpass"),
        is_active=True,
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)
    return teacher


@pytest.fixture
def seed_school_class(db_session):
    """Create a test SchoolClass. Returns the SchoolClass object."""
    from app.models.school_class import SchoolClass

    sc = SchoolClass(name="10A")
    db_session.add(sc)
    db_session.commit()
    db_session.refresh(sc)
    return sc


@pytest.fixture
def teacher_client(test_client, seed_teacher):
    """Authenticated TestClient as teacher. Follows admin_client pattern."""
    resp = test_client.post(
        "/auth/login",
        data={"email": "teacher@test.com", "password": "teacherpass", "next": ""},
    )
    assert resp.status_code == 303, f"Teacher login failed: {resp.status_code}"
    return test_client


@pytest.fixture
def seed_schedule_entry(db_session, seed_device, seed_teacher):
    """Seed a ScheduleEntry for today (always matches current weekday)."""
    entry = ScheduleEntry(
        device_id=seed_device.id,
        teacher_id=seed_teacher.id,
        class_name="10A",
        weekday=date.today().weekday(),
        start_time=time(8, 0),
        end_time=time(9, 30),
    )
    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)
    return entry


@pytest.fixture
def seed_students(db_session):
    """Seed 3 active students in class 10A."""
    students = []
    for email, first, last in [
        ("student1@test.com", "Max", "Mueller"),
        ("student2@test.com", "Anna", "Schmidt"),
        ("student3@test.com", "Lisa", "Weber"),
    ]:
        s = User(
            email=email,
            first_name=first,
            last_name=last,
            role="student",
            class_name="10A",
            password_hash=get_password_hash("studentpass"),
            is_active=True,
        )
        db_session.add(s)
        students.append(s)
    db_session.commit()
    for s in students:
        db_session.refresh(s)
    return students


@pytest.fixture
def seed_token(db_session, seed_schedule_entry):
    """Seed an AttendanceToken for today's schedule entry."""
    token = AttendanceToken(
        token=str(uuid.uuid4()),
        device_id=seed_schedule_entry.device_id,
        schedule_entry_id=seed_schedule_entry.id,
        lesson_date=date.today(),
        is_active=True,
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=2),
    )
    db_session.add(token)
    db_session.commit()
    db_session.refresh(token)
    return token


@pytest.fixture
def seed_attendance(db_session, seed_token, seed_students):
    """Seed attendance records for first 2 students."""
    records = []
    for student in seed_students[:2]:
        record = AttendanceRecord(
            student_id=student.id,
            token_id=seed_token.id,
            checked_in_at=datetime.now(),
        )
        db_session.add(record)
        records.append(record)
    db_session.commit()
    for r in records:
        db_session.refresh(r)
    return records


@pytest.fixture
def student_client(test_client, seed_students):
    """Authenticated TestClient as first seed student."""
    resp = test_client.post(
        "/auth/login",
        data={"email": "student1@test.com", "password": "studentpass", "next": ""},
    )
    assert resp.status_code == 303
    return test_client
