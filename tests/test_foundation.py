"""
Tests for Phase 1: Foundation requirements.
FOUND-01: directory structure
FOUND-02: config loads from .env
FOUND-03: database session factory
FOUND-04: all 5 tables created  (xfail until Plan 02 adds models)
FOUND-08: .env.example completeness
"""
import os
import pytest


# ── FOUND-01: Directory structure ──────────────────────────────────────────

def test_directory_structure():
    """All required directories must exist relative to project root."""
    required = [
        "app",
        "app/models",
        "app/routers",
        "app/services",
        "app/templates",
        "app/static",
        "dummy_client",
        "mosquitto/config",
    ]
    for path in required:
        assert os.path.isdir(path), f"Missing required directory: {path}"


# ── FOUND-02: Config loads ──────────────────────────────────────────────────

def test_config_loads():
    """Settings must load without error; types must be correct."""
    from app.config import get_settings
    settings = get_settings()
    assert settings.database_url.startswith("sqlite"), (
        f"database_url should start with 'sqlite', got: {settings.database_url}"
    )
    assert isinstance(settings.mqtt_port, int), "mqtt_port must be int"
    assert settings.mqtt_port == 1883
    assert settings.secret_key == "test-secret-key-for-pytest-only"


# ── FOUND-03: Database session ──────────────────────────────────────────────

def test_database_session():
    """get_db() must yield a SQLAlchemy Session."""
    from sqlalchemy.orm import Session
    from app.database import get_db
    db_gen = get_db()
    db = next(db_gen)
    assert isinstance(db, Session), f"Expected Session, got {type(db)}"
    # Clean up
    try:
        next(db_gen)
    except StopIteration:
        pass


# ── FOUND-04: All 5 tables (xfail until Plan 02 adds models) ───────────────

@pytest.mark.xfail(reason="Models not yet created — becomes passing after Plan 02", strict=False)
def test_all_tables_created():
    """After create_all(), Base.metadata must have exactly 5 tables."""
    from app.database import Base, engine
    import app.models  # noqa: F401 — triggers model registration
    Base.metadata.create_all(bind=engine)
    table_names = set(Base.metadata.tables.keys())
    expected = {"users", "devices", "schedule_entries", "attendance_tokens", "attendance_records"}
    assert table_names == expected, (
        f"Table mismatch. Found: {table_names}, expected: {expected}"
    )


# ── FOUND-08: .env.example completeness ────────────────────────────────────

def test_env_example_complete():
    """.env.example must document all required environment variables."""
    env_example_path = ".env.example"
    if not os.path.exists(env_example_path):
        pytest.skip(".env.example not yet created — pending Plan 03")
    with open(env_example_path) as f:
        content = f.read()
    required_vars = ["SECRET_KEY", "DATABASE_URL", "MQTT_BROKER", "MQTT_PORT", "SERVER_IP"]
    for var in required_vars:
        assert var in content, f".env.example missing variable: {var}"
