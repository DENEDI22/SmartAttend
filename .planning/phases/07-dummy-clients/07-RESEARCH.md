# Phase 7: Dummy Clients - Research

**Researched:** 2026-03-30
**Domain:** Python MQTT client (paho-mqtt v2), Docker containerization
**Confidence:** HIGH

## Summary

This phase replaces the Phase 1 stub (`dummy_client/main.py`) with a fully functional MQTT client that simulates an ESP32 device. The client publishes registration, heartbeat, and lux messages on the topics defined in Phase 6, and subscribes to receive token URLs. The implementation is a single Python file using `paho-mqtt==2.1.0` (already in the project) with the v2 callback API matching the server pattern.

The Docker infrastructure is already in place: `docker-compose.yml` defines three client containers (client-e101, client-e102, client-e103) with all required environment variables. The `dummy_client/Dockerfile` needs only the addition of `paho-mqtt` installation. No other dependencies are required.

**Primary recommendation:** Implement a single `dummy_client/main.py` using paho-mqtt v2 `CallbackAPIVersion.VERSION2`, with `threading.Event` for periodic publish scheduling and `signal` for graceful SIGTERM shutdown. Add `requirements.txt` to `dummy_client/` with `paho-mqtt==2.1.0` for clean dependency management.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
User chose "You decide on all" -- Claude has full flexibility on all implementation decisions.

**Locked from Phase 6 (not negotiable):**
- Registration: publish to `devices/register` with JSON `{"device_id": "<id>"}` or plain device_id
- Heartbeat: publish to `devices/{device_id}/status` every 30 seconds, QoS 0
- Lux: publish to `sensors/{device_id}/lux` every 60 seconds with configurable value, QoS 0
- Token subscription: subscribe to `attendance/device/{device_id}`, QoS 1
- Environment variables: `DEVICE_ID`, `ROOM`, `MQTT_BROKER`, `MQTT_PORT`, `LUX_VALUE`

### Claude's Discretion
- Client startup logging format and content
- Heartbeat payload content
- Lux value: exact or slight randomization around LUX_VALUE
- Token URL printing format
- Reconnection and resilience strategy
- Graceful shutdown handling (SIGTERM)
- Dockerfile changes
- paho-mqtt v2 API vs v1 style
- Internal code structure (threading, scheduling)
- Separate requirements.txt vs inline install

### Deferred Ideas (OUT OF SCOPE)
None.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DUMMY-01 | Publishes `devices/register` on startup | Registration pattern in Architecture Patterns; JSON payload matches server's `_handle_register` |
| DUMMY-02 | Publishes `devices/{id}/status` heartbeat every 30s | Timer loop pattern; server `_handle_heartbeat` expects any payload |
| DUMMY-03 | Publishes `sensors/{id}/lux` every 60s with configurable value | LUX_VALUE env var; server `_handle_lux` expects `float(payload)` |
| DUMMY-04 | Subscribes to `attendance/device/{id}` and prints URL | on_message callback; QoS 1 subscription in on_connect |
| DUMMY-05 | Fully configured via env vars | All 5 env vars already in docker-compose.yml |
| DUMMY-06 | Dockerfile exists and included in docker-compose.yml | Existing Dockerfile needs paho-mqtt; compose already references `./dummy_client` |
| DUMMY-07 | Three instances run as separate containers | docker-compose.yml already defines all three |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| paho-mqtt | 2.1.0 | MQTT client | Already used by server; standard Python MQTT library |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| threading | stdlib | Event-based sleep for periodic publishes | Graceful shutdown via Event.wait() instead of time.sleep() |
| signal | stdlib | SIGTERM handler for Docker stop | Clean disconnect from broker |
| json | stdlib | JSON registration payload | Registration message format |
| os | stdlib | Environment variable reading | All 5 config values |
| logging | stdlib | Structured log output | Consistent with server logging style |

No additional pip packages needed beyond paho-mqtt.

**Installation (dummy_client/requirements.txt):**
```
paho-mqtt==2.1.0
```

## Architecture Patterns

### Recommended Project Structure
```
dummy_client/
  main.py            # Single-file client (all logic)
  requirements.txt   # paho-mqtt==2.1.0
  Dockerfile         # python:3.11-slim + requirements.txt + main.py
```

### Pattern 1: paho-mqtt v2 Callback API (matching server)
**What:** Use `CallbackAPIVersion.VERSION2` for consistency with server-side `app/services/mqtt.py`.
**When to use:** Always -- the entire project uses v2.

```python
import paho.mqtt.client as mqtt

client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id=f"dummy-{device_id}",
)
```

v2 callback signatures:
- `on_connect(client, userdata, connect_flags, reason_code, properties)`
- `on_message(client, userdata, message)`
- `on_disconnect(client, userdata, disconnect_flags, reason_code, properties)`

### Pattern 2: Subscribe in on_connect for Auto-Resubscription
**What:** Subscribe to topics inside the `on_connect` callback so reconnects automatically resubscribe.
**When to use:** Always -- same pattern as server.

```python
def on_connect(client, userdata, connect_flags, reason_code, properties):
    if reason_code == 0:
        client.subscribe(f"attendance/device/{device_id}", qos=1)
        logging.info("Connected and subscribed")
```

### Pattern 3: threading.Event for Interruptible Periodic Tasks
**What:** Use `Event.wait(timeout)` instead of `time.sleep()` for periodic publishes. This allows graceful shutdown by setting the event.
**When to use:** For the heartbeat (30s) and lux (60s) publish loops.

```python
import threading

stop_event = threading.Event()

def heartbeat_loop():
    while not stop_event.is_set():
        client.publish(f"devices/{device_id}/status", "online", qos=0)
        stop_event.wait(30)

def lux_loop():
    while not stop_event.is_set():
        client.publish(f"sensors/{device_id}/lux", str(lux_value), qos=0)
        stop_event.wait(60)
```

### Pattern 4: SIGTERM Handler for Docker Stop
**What:** Docker sends SIGTERM on `docker compose stop/down`. Catch it to disconnect cleanly.

```python
import signal

def shutdown(signum, frame):
    logging.info("Shutting down...")
    stop_event.set()

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)
```

### Pattern 5: Registration on Connect (Not Just Startup)
**What:** Publish the registration message inside `on_connect` rather than after `client.connect()`. This ensures re-registration after reconnect.

### Anti-Patterns to Avoid
- **time.sleep() in main loop:** Not interruptible by SIGTERM -- use `Event.wait()` instead.
- **Connecting before setting callbacks:** Set `on_connect`, `on_message` before calling `client.connect()`.
- **Using loop_forever() with separate threads:** `loop_start()` + main-thread wait is simpler and plays better with signal handling.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MQTT reconnection | Custom retry logic | paho-mqtt built-in `reconnect_delay_set(min_delay=1, max_delay=30)` | Already handles exponential backoff |
| Periodic scheduling | APScheduler or cron | Simple `threading.Event.wait(N)` loops | No need for a scheduler library for 2 timers |
| JSON serialization | String concatenation | `json.dumps({"device_id": device_id})` | Correct escaping |

## Common Pitfalls

### Pitfall 1: Broker Not Ready at Container Start
**What goes wrong:** Dummy client starts before Mosquitto is ready (Docker `depends_on` only waits for container start, not port readiness).
**Why it happens:** Docker Compose `depends_on` does not check health.
**How to avoid:** paho-mqtt's `reconnect_on_failure=True` (default) + `reconnect_delay_set()` handles this automatically. The client will retry until the broker is up.
**Warning signs:** "Connection refused" in first few seconds of client log -- this is EXPECTED and resolves automatically.

### Pitfall 2: Threads Not Daemon = Container Hangs on Stop
**What goes wrong:** Non-daemon threads prevent Python from exiting on SIGTERM.
**Why it happens:** Default `threading.Thread(daemon=False)`.
**How to avoid:** Set `daemon=True` on heartbeat and lux threads, or use `stop_event.set()` + `thread.join(timeout)` in shutdown handler.

### Pitfall 3: Lux Payload Must Be Parseable as Float
**What goes wrong:** Server calls `float(payload)` in `_handle_lux` -- non-numeric strings cause exceptions.
**Why it happens:** Sending JSON or non-numeric lux values.
**How to avoid:** Always send plain numeric string: `str(lux_value)` e.g. `"400"` or `"400.0"`.

### Pitfall 4: QoS Mismatch
**What goes wrong:** Using QoS 1 for heartbeat/lux wastes broker resources; using QoS 0 for token subscription risks missing token URLs.
**Why it happens:** Not matching the Phase 6 contract.
**How to avoid:** Heartbeat and lux = QoS 0. Token subscription = QoS 1. Locked in Phase 6.

### Pitfall 5: Flush Required for Docker Logs
**What goes wrong:** Print statements don't appear in `docker compose logs` because Python buffers stdout.
**Why it happens:** Python's default stdout buffering in non-interactive mode.
**How to avoid:** Use `logging` (which writes to stderr, unbuffered by default) or set `PYTHONUNBUFFERED=1` in Dockerfile ENV, or use `flush=True` on print().

## Code Examples

### Complete Client Structure (Verified Against Server Contract)

```python
"""Dummy MQTT client simulating an ESP32 device."""
import json
import logging
import os
import signal
import threading

import paho.mqtt.client as mqtt

# Config from environment
DEVICE_ID = os.environ.get("DEVICE_ID", "unknown")
ROOM = os.environ.get("ROOM", "unknown")
MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
LUX_VALUE = float(os.environ.get("LUX_VALUE", "400"))

logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s [{DEVICE_ID}] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

stop_event = threading.Event()


def on_connect(client, userdata, connect_flags, reason_code, properties):
    if reason_code == 0:
        logger.info("Connected to broker %s:%d", MQTT_BROKER, MQTT_PORT)
        # Register on every (re)connect
        client.publish("devices/register", json.dumps({"device_id": DEVICE_ID}), qos=0)
        logger.info("Published registration")
        # Subscribe to token topic
        client.subscribe(f"attendance/device/{DEVICE_ID}", qos=1)
        logger.info("Subscribed to attendance/device/%s", DEVICE_ID)
    else:
        logger.error("Connection failed: reason_code=%s", reason_code)


def on_message(client, userdata, message):
    url = message.payload.decode("utf-8")
    logger.info("TOKEN URL RECEIVED: %s", url)


def heartbeat_loop(client):
    while not stop_event.is_set():
        if client.is_connected():
            client.publish(f"devices/{DEVICE_ID}/status", "online", qos=0)
            logger.debug("Heartbeat sent")
        stop_event.wait(30)


def lux_loop(client):
    while not stop_event.is_set():
        if client.is_connected():
            client.publish(f"sensors/{DEVICE_ID}/lux", str(LUX_VALUE), qos=0)
            logger.debug("Lux sent: %s", LUX_VALUE)
        stop_event.wait(60)


def main():
    logger.info("Starting dummy client %s (room=%s, lux=%s)", DEVICE_ID, ROOM, LUX_VALUE)

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"dummy-{DEVICE_ID}",
    )
    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    # Graceful shutdown
    def shutdown(signum, frame):
        logger.info("Received signal %s, shutting down...", signum)
        stop_event.set()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    # Start background threads
    hb_thread = threading.Thread(target=heartbeat_loop, args=(client,), daemon=True)
    lux_thread = threading.Thread(target=lux_loop, args=(client,), daemon=True)
    hb_thread.start()
    lux_thread.start()

    # Connect (retries automatically on failure)
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    except (ConnectionRefusedError, OSError) as e:
        logger.warning("Broker not available, will retry: %s", e)

    client.loop_start()

    # Block main thread until shutdown signal
    stop_event.wait()

    client.loop_stop()
    client.disconnect()
    logger.info("Client %s stopped", DEVICE_ID)


if __name__ == "__main__":
    main()
```

### Dockerfile Pattern

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
ENV PYTHONUNBUFFERED=1
CMD ["python", "main.py"]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| paho-mqtt v1 callbacks | paho-mqtt v2 `CallbackAPIVersion.VERSION2` | paho-mqtt 2.0 (2024) | Different callback signatures; v1 deprecated |
| `client.loop_forever()` blocking | `client.loop_start()` + main thread control | Always available | Allows clean shutdown with signals |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (via existing test suite) |
| Config file | tests/conftest.py (existing) |
| Quick run command | `python -m pytest tests/test_dummy_client.py -x -q` |
| Full suite command | `python -m pytest tests/ -x -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DUMMY-01 | Registration on connect | unit (mock) | `pytest tests/test_dummy_client.py::test_registration_on_connect -x` | Wave 0 |
| DUMMY-02 | Heartbeat every 30s | unit (mock) | `pytest tests/test_dummy_client.py::test_heartbeat_publishes -x` | Wave 0 |
| DUMMY-03 | Lux publish every 60s | unit (mock) | `pytest tests/test_dummy_client.py::test_lux_publishes -x` | Wave 0 |
| DUMMY-04 | Token URL printed on receive | unit (mock) | `pytest tests/test_dummy_client.py::test_token_url_logged -x` | Wave 0 |
| DUMMY-05 | Env var configuration | unit | `pytest tests/test_dummy_client.py::test_env_config -x` | Wave 0 |
| DUMMY-06 | Dockerfile builds | manual-only | `docker compose build client-e101` | N/A |
| DUMMY-07 | Three containers start | manual-only | `docker compose up -d client-e101 client-e102 client-e103` | N/A |

### Testing Strategy
The dummy client is a standalone script (not part of the FastAPI app). Tests should:
- Import functions from `dummy_client.main` (add `dummy_client/` to sys.path or use importlib)
- Mock `paho.mqtt.client.Client` to verify publish/subscribe calls
- Use `unittest.mock.patch` for MQTT client, `monkeypatch` for env vars
- Test `on_connect` callback publishes registration and subscribes to token topic
- Test `on_message` callback logs the received URL
- Test heartbeat/lux loops with mocked client (call function, verify publish)

**Note:** DUMMY-06 and DUMMY-07 are infrastructure tests verified manually via `docker compose up`.

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_dummy_client.py -x -q`
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green + manual `docker compose up` verification

### Wave 0 Gaps
- [ ] `tests/test_dummy_client.py` -- covers DUMMY-01 through DUMMY-05
- [ ] Import mechanism for `dummy_client/main.py` from test suite (sys.path manipulation or conftest fixture)

## Project Constraints (from CLAUDE.md)

- **Hardware**: No ESP32 -- everything via Python dummy clients (this phase)
- **Tech Stack**: paho-mqtt (already in use)
- **Runtime**: Raspberry Pi ARM -- Docker images must be multi-arch (python:3.11-slim is multi-arch)
- **CSS**: Not applicable to this phase
- **Database**: Not applicable (dummy client has no DB access)

## Sources

### Primary (HIGH confidence)
- `app/services/mqtt.py` -- Server-side MQTT contract (on_connect, _handle_register, _handle_heartbeat, _handle_lux, publish_token)
- `docker-compose.yml` -- Container definitions with env vars
- `dummy_client/main.py` -- Current stub to replace
- `dummy_client/Dockerfile` -- Current Dockerfile to update
- `requirements.txt` -- paho-mqtt==2.1.0 pinned
- paho-mqtt 2.1.0 installed locally -- v2 API verified via `help(mqtt.Client.__init__)`

### Secondary (MEDIUM confidence)
- paho-mqtt v2 callback signatures verified from installed package

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- single dependency (paho-mqtt) already used by server, version verified
- Architecture: HIGH -- direct mirror of server patterns, single-file client
- Pitfalls: HIGH -- common Docker/MQTT issues well-documented in project history

**Research date:** 2026-03-30
**Valid until:** 2026-04-30 (stable domain, no moving parts)
