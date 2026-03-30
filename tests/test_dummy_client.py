"""Unit tests for dummy MQTT client (DUMMY-01 through DUMMY-05)."""
import json
import logging
import os
import sys
import threading
from unittest.mock import MagicMock, patch

import pytest

# Add dummy_client to sys.path so we can import main
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "dummy_client"))


def _reload_main(monkeypatch, **env_overrides):
    """Helper: set env vars and (re)load dummy_client.main module."""
    defaults = {
        "DEVICE_ID": "e101",
        "ROOM": "E101",
        "MQTT_BROKER": "localhost",
        "MQTT_PORT": "1883",
        "LUX_VALUE": "400",
    }
    defaults.update(env_overrides)
    for k, v in defaults.items():
        monkeypatch.setenv(k, v)

    import importlib
    # Remove cached module so reload picks up new env vars
    if "main" in sys.modules:
        del sys.modules["main"]
    import main as dummy_main
    return dummy_main


class TestEnvConfig:
    """DUMMY-05: All behavior configured via environment variables."""

    def test_env_config(self, monkeypatch):
        mod = _reload_main(
            monkeypatch,
            DEVICE_ID="test-dev",
            ROOM="R999",
            MQTT_BROKER="broker.local",
            MQTT_PORT="9999",
            LUX_VALUE="123.5",
        )
        assert mod.DEVICE_ID == "test-dev"
        assert mod.ROOM == "R999"
        assert mod.MQTT_BROKER == "broker.local"
        assert mod.MQTT_PORT == 9999
        assert mod.LUX_VALUE == 123.5


class TestRegistrationOnConnect:
    """DUMMY-01: Publish registration JSON on connect."""

    def test_registration_on_connect(self, monkeypatch):
        mod = _reload_main(monkeypatch, DEVICE_ID="e101")
        mock_client = MagicMock()

        # Call on_connect with reason_code=0 (success)
        mod.on_connect(mock_client, None, MagicMock(), 0, None)

        # Should publish registration JSON
        mock_client.publish.assert_called_once()
        call_args = mock_client.publish.call_args
        assert call_args[0][0] == "devices/register" or call_args.kwargs.get("topic") == "devices/register"
        payload = call_args[0][1] if len(call_args[0]) > 1 else call_args.kwargs.get("payload")
        data = json.loads(payload)
        assert data["device_id"] == "e101"

        # Should subscribe to token topic
        mock_client.subscribe.assert_called_once()
        sub_args = mock_client.subscribe.call_args
        assert "attendance/device/e101" in str(sub_args)

    def test_on_connect_failure(self, monkeypatch):
        """Robustness: on_connect with failure reason_code should not publish."""
        mod = _reload_main(monkeypatch, DEVICE_ID="e101")
        mock_client = MagicMock()

        # Call with non-zero reason_code (failure)
        mod.on_connect(mock_client, None, MagicMock(), 1, None)

        mock_client.publish.assert_not_called()
        mock_client.subscribe.assert_not_called()


class TestHeartbeat:
    """DUMMY-02: Publish heartbeat every 30s."""

    def test_heartbeat_publishes(self, monkeypatch):
        mod = _reload_main(monkeypatch, DEVICE_ID="e101")
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True

        # Create a stop_event that allows one iteration then stops
        stop = threading.Event()
        call_count = 0
        original_wait = stop.wait

        def limited_wait(timeout=None):
            nonlocal call_count
            call_count += 1
            if call_count >= 1:
                stop.set()
            return stop.is_set()

        stop.wait = limited_wait

        # Patch the module-level stop_event
        monkeypatch.setattr(mod, "stop_event", stop)

        mod.heartbeat_loop(mock_client)

        # Should have published heartbeat
        mock_client.publish.assert_called_once()
        call_args = mock_client.publish.call_args
        topic = call_args[0][0]
        payload = call_args[0][1] if len(call_args[0]) > 1 else call_args.kwargs.get("payload")
        assert topic == "devices/e101/status"
        assert payload == "online"


class TestLux:
    """DUMMY-03: Publish lux reading every 60s."""

    def test_lux_publishes(self, monkeypatch):
        mod = _reload_main(monkeypatch, DEVICE_ID="e101", LUX_VALUE="400")
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True

        # Create a stop_event that allows one iteration then stops
        stop = threading.Event()
        call_count = 0

        def limited_wait(timeout=None):
            nonlocal call_count
            call_count += 1
            if call_count >= 1:
                stop.set()
            return stop.is_set()

        stop.wait = limited_wait
        monkeypatch.setattr(mod, "stop_event", stop)

        mod.lux_loop(mock_client)

        mock_client.publish.assert_called_once()
        call_args = mock_client.publish.call_args
        topic = call_args[0][0]
        payload = call_args[0][1] if len(call_args[0]) > 1 else call_args.kwargs.get("payload")
        assert topic == "sensors/e101/lux"
        # Payload must be parseable as float
        assert float(payload) == 400.0


class TestTokenUrl:
    """DUMMY-04: Subscribe to token URL topic and log received URLs."""

    def test_token_url_logged(self, monkeypatch, caplog):
        mod = _reload_main(monkeypatch, DEVICE_ID="e101")

        mock_msg = MagicMock()
        mock_msg.topic = "attendance/device/e101"
        mock_msg.payload = b"http://127.0.0.1/checkin?token=abc123"

        with caplog.at_level(logging.INFO):
            mod.on_message(None, None, mock_msg)

        assert "http://127.0.0.1/checkin?token=abc123" in caplog.text
