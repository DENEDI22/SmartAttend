"""MQTT service module -- stub for TDD RED phase."""
import paho.mqtt.client as mqtt

from app.database import SessionLocal

_client: mqtt.Client | None = None


def _on_connect(client, userdata, connect_flags, reason_code, properties):
    pass


def _on_message(client, userdata, message):
    pass


def _handle_register(payload: str):
    pass


def _handle_heartbeat(device_id: str, payload: str):
    pass


def _handle_lux(device_id: str, payload: str):
    pass


def publish_token(device_id: str, url: str):
    pass


def start_mqtt():
    pass


def stop_mqtt():
    pass
