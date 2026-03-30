"""Dummy MQTT client simulating an ESP32 device for SmartAttend.

Publishes registration on connect, heartbeat every 30s, lux every 60s.
Subscribes to token URL topic and logs received URLs.
Configured entirely via environment variables.
"""
import json
import logging
import os
import signal
import threading

import paho.mqtt.client as mqtt

# ---------------------------------------------------------------------------
# Environment configuration (DUMMY-05)
# ---------------------------------------------------------------------------
DEVICE_ID = os.environ.get("DEVICE_ID", "unknown")
ROOM = os.environ.get("ROOM", "unknown")
MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
LUX_VALUE = float(os.environ.get("LUX_VALUE", "400"))

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    format=f"%(asctime)s [{DEVICE_ID}] %(levelname)s %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Graceful shutdown
# ---------------------------------------------------------------------------
stop_event = threading.Event()


# ---------------------------------------------------------------------------
# MQTT callbacks (paho v2 signatures)
# ---------------------------------------------------------------------------
def on_connect(client, userdata, connect_flags, reason_code, properties):
    """DUMMY-01: Publish registration and subscribe to token topic on connect."""
    if reason_code == 0:
        payload = json.dumps({"device_id": DEVICE_ID})
        client.publish("devices/register", payload, qos=0)
        logger.info("Published registration to devices/register")
        client.subscribe(f"attendance/device/{DEVICE_ID}", qos=1)
        logger.info("Subscribed to attendance/device/%s", DEVICE_ID)
    else:
        logger.error("Connection failed with reason_code=%s", reason_code)


def on_message(client, userdata, message):
    """DUMMY-04: Log received token URL."""
    url = message.payload.decode("utf-8")
    logger.info("TOKEN URL RECEIVED: %s", url)


# ---------------------------------------------------------------------------
# Periodic loops (run in daemon threads)
# ---------------------------------------------------------------------------
def heartbeat_loop(client):
    """DUMMY-02: Publish heartbeat every 30 seconds."""
    while not stop_event.is_set():
        if client.is_connected():
            client.publish(f"devices/{DEVICE_ID}/status", "online", qos=0)
            logger.debug("Heartbeat sent")
        stop_event.wait(30)


def lux_loop(client):
    """DUMMY-03: Publish lux reading every 60 seconds."""
    while not stop_event.is_set():
        if client.is_connected():
            client.publish(f"sensors/{DEVICE_ID}/lux", str(LUX_VALUE), qos=0)
            logger.debug("Lux reading sent: %s", LUX_VALUE)
        stop_event.wait(60)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main():
    """Start the dummy MQTT client."""
    logger.info("Starting dummy client: device=%s room=%s lux=%s", DEVICE_ID, ROOM, LUX_VALUE)

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"dummy-{DEVICE_ID}",
    )
    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    # Graceful shutdown on SIGTERM / SIGINT
    def _shutdown(signum, frame):
        logger.info("Received signal %s, shutting down...", signum)
        stop_event.set()

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    # Start periodic loops as daemon threads
    threading.Thread(target=heartbeat_loop, args=(client,), daemon=True).start()
    threading.Thread(target=lux_loop, args=(client,), daemon=True).start()

    # Connect to MQTT broker
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    except (ConnectionRefusedError, OSError) as exc:
        logger.warning("MQTT broker not available at %s:%s — will retry: %s", MQTT_BROKER, MQTT_PORT, exc)

    client.loop_start()
    logger.info("MQTT loop started, waiting for shutdown signal...")

    # Block until shutdown signal
    stop_event.wait()

    client.loop_stop()
    client.disconnect()
    logger.info("Dummy client %s shut down cleanly", DEVICE_ID)


if __name__ == "__main__":
    main()
