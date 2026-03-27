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
