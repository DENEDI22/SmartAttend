"""Phase 1 stub — keeps the container alive.
Real implementation (MQTT publish/subscribe) is added in Phase 7.
"""
import time
import os

device_id = os.environ.get("DEVICE_ID", "unknown")
room = os.environ.get("ROOM", "unknown")

print(f"[stub] dummy_client {device_id} (room {room}) running — Phase 1 placeholder", flush=True)

while True:
    time.sleep(60)
