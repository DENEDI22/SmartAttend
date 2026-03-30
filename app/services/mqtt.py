"""MQTT service module: subscribes to device topics, handles registration/heartbeat/lux, publishes tokens."""
import json
import logging
from datetime import datetime

import paho.mqtt.client as mqtt

from app.config import get_settings
from app.database import SessionLocal
from app.models.device import Device

logger = logging.getLogger(__name__)

_client: mqtt.Client | None = None


def _on_connect(client, userdata, connect_flags, reason_code, properties):
    """Subscribe to device topics on successful connection."""
    if reason_code == 0:
        client.subscribe([
            ("devices/register", 0),
            ("devices/+/status", 0),
            ("sensors/+/lux", 0),
        ])
        logger.info("MQTT connected and subscribed to device topics")
    else:
        logger.error("MQTT connection failed with reason_code=%s", reason_code)


def _on_message(client, userdata, message):
    """Route incoming messages to the appropriate handler."""
    try:
        payload = message.payload.decode("utf-8")
        topic = message.topic

        if topic == "devices/register":
            _handle_register(payload)
        elif topic.startswith("devices/") and topic.endswith("/status"):
            # devices/{device_id}/status
            parts = topic.split("/")
            device_id = parts[1]
            _handle_heartbeat(device_id, payload)
        elif topic.startswith("sensors/") and topic.endswith("/lux"):
            # sensors/{device_id}/lux
            parts = topic.split("/")
            device_id = parts[1]
            _handle_lux(device_id, payload)
    except Exception:
        logger.exception("Error processing MQTT message on topic %s", message.topic)


def _handle_register(payload: str):
    """Register a new device from JSON payload. Idempotent -- skips if device exists."""
    try:
        data = json.loads(payload)
        device_id = data["device_id"]
    except (json.JSONDecodeError, KeyError):
        device_id = payload.strip()

    db = SessionLocal()
    try:
        existing = db.query(Device).filter_by(device_id=device_id).first()
        if existing:
            return
        device = Device(device_id=device_id, is_enabled=False, is_online=False)
        db.add(device)
        db.commit()
        logger.info("Registered new device: %s", device_id)
    finally:
        db.close()


def _handle_heartbeat(device_id: str, payload: str):
    """Update device online status and last_seen timestamp.

    Auto-creates the device if it doesn't exist yet (handles the case where
    the client started before the server and the registration message was missed).
    """
    db = SessionLocal()
    try:
        device = db.query(Device).filter_by(device_id=device_id).first()
        if not device:
            device = Device(device_id=device_id, is_enabled=False, is_online=True, last_seen=datetime.now())
            db.add(device)
            db.commit()
            logger.info("Auto-registered device from heartbeat: %s", device_id)
            return
        device.is_online = True
        device.last_seen = datetime.now()
        db.commit()
    finally:
        db.close()


def _handle_lux(device_id: str, payload: str):
    """Update device lux reading."""
    db = SessionLocal()
    try:
        device = db.query(Device).filter_by(device_id=device_id).first()
        if not device:
            return
        device.last_lux = float(payload)
        db.commit()
    finally:
        db.close()


def publish_token(device_id: str, url: str):
    """Publish a token URL to a device's attendance topic with QoS 1."""
    if _client and _client.is_connected():
        _client.publish(
            f"attendance/device/{device_id}",
            url,
            qos=1,
        )


def start_mqtt():
    """Start the MQTT client with threaded background loop."""
    global _client
    settings = get_settings()
    _client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    _client.on_connect = _on_connect
    _client.on_message = _on_message
    _client.reconnect_delay_set(min_delay=1, max_delay=30)
    try:
        _client.connect(settings.mqtt_broker, settings.mqtt_port, keepalive=60)
        _client.loop_start()
        logger.info("MQTT client started, connecting to %s:%d", settings.mqtt_broker, settings.mqtt_port)
    except (ConnectionRefusedError, OSError) as e:
        logger.warning("MQTT broker not available at %s:%s — will retry: %s",
                       settings.mqtt_broker, settings.mqtt_port, e)


def stop_mqtt():
    """Stop the MQTT client and clean up."""
    global _client
    if _client:
        _client.loop_stop()
        _client.disconnect()
        _client = None
        logger.info("MQTT client stopped")
