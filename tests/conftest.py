import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
    # Clear lru_cache so each test gets fresh settings
    from app.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
