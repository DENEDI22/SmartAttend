"""Tests for MQTT service module."""
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.models.device import Device


class _NonClosingSession:
    """Wraps a real session but makes close() a no-op so the test can still inspect objects."""

    def __init__(self, real):
        self._real = real

    def close(self):
        # no-op: keep session open for test assertions
        pass

    def __getattr__(self, name):
        return getattr(self._real, name)


@pytest.fixture
def mock_session_local(db_session):
    """Make mqtt handlers use the test DB session (with no-op close)."""
    def _factory():
        return _NonClosingSession(db_session)
    return _factory


@pytest.fixture
def patch_session(mock_session_local, monkeypatch):
    """Monkeypatch SessionLocal in mqtt module."""
    import app.services.mqtt as mqtt_mod
    monkeypatch.setattr(mqtt_mod, "SessionLocal", mock_session_local)


def test_subscribe_topics(override_settings):
    """Mock paho client, call _on_connect, verify subscribe called with correct topics."""
    from app.services.mqtt import _on_connect

    mock_client = MagicMock()
    _on_connect(mock_client, None, None, 0, None)

    mock_client.subscribe.assert_called_once_with([
        ("devices/register", 0),
        ("devices/+/status", 0),
        ("sensors/+/lux", 0),
    ])


def test_register_device_json(db_session, patch_session):
    """Register a device via JSON payload, verify Device created."""
    from app.services.mqtt import _handle_register

    _handle_register(json.dumps({"device_id": "e101"}))

    device = db_session.query(Device).filter_by(device_id="e101").first()
    assert device is not None
    assert device.device_id == "e101"
    assert device.is_enabled is False
    assert device.is_online is False


def test_register_device_duplicate(db_session, patch_session):
    """Registering same device_id twice should be idempotent (1 row)."""
    from app.services.mqtt import _handle_register

    _handle_register(json.dumps({"device_id": "e101"}))
    _handle_register(json.dumps({"device_id": "e101"}))

    count = db_session.query(Device).filter_by(device_id="e101").count()
    assert count == 1


def test_heartbeat_update(db_session, patch_session):
    """Heartbeat sets is_online=True and updates last_seen."""
    from app.services.mqtt import _handle_heartbeat

    device = Device(device_id="e101", is_enabled=False, is_online=False)
    db_session.add(device)
    db_session.commit()

    _handle_heartbeat("e101", "online")

    db_session.refresh(device)
    assert device.is_online is True
    assert device.last_seen is not None


def test_heartbeat_unknown_device(db_session, patch_session):
    """Heartbeat for unknown device should not raise."""
    from app.services.mqtt import _handle_heartbeat

    _handle_heartbeat("unknown_device", "online")


def test_lux_update(db_session, patch_session):
    """Lux message updates device.last_lux."""
    from app.services.mqtt import _handle_lux

    device = Device(device_id="e101", is_enabled=False, is_online=False)
    db_session.add(device)
    db_session.commit()

    _handle_lux("e101", "450.5")

    db_session.refresh(device)
    assert device.last_lux == 450.5


def test_publish_token(override_settings):
    """publish_token publishes to correct topic with QoS 1."""
    import app.services.mqtt as mqtt_mod
    from app.services.mqtt import publish_token

    mock_client = MagicMock()
    mock_client.is_connected.return_value = True
    mqtt_mod._client = mock_client

    try:
        publish_token("e101", "http://127.0.0.1/checkin?token=abc")

        mock_client.publish.assert_called_once_with(
            "attendance/device/e101",
            "http://127.0.0.1/checkin?token=abc",
            qos=1,
        )
    finally:
        mqtt_mod._client = None
