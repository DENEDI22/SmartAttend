import os
import pytest
import app.database as _app_database
import app.main as _app_main
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, get_db

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
    from app.services.auth import get_password_hash
    from app.models.user import User

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


@pytest.fixture
def seed_device(db_session):
    """Create a test device. Returns the Device object."""
    from app.models.device import Device

    device = Device(
        device_id="test-device-001",
        room="R101",
        label="Raum 101",
        is_enabled=False,
        is_online=True,
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


@pytest.fixture
def seed_teacher(db_session):
    """Create a test teacher. Returns the User object."""
    from app.services.auth import get_password_hash
    from app.models.user import User

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
