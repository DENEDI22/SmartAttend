# Phase 6: MQTT & Scheduler - Research

**Researched:** 2026-03-30
**Domain:** MQTT pub/sub integration, background job scheduling, device lifecycle management
**Confidence:** HIGH

## Summary

This phase connects the FastAPI server to the Mosquitto MQTT broker using paho-mqtt 2.1.0 (already pinned) and schedules token issuance using APScheduler 3.11.2 (already pinned). The server subscribes to three topic patterns for device registration, heartbeat, and lux data, and publishes token URLs to per-device attendance topics. A scheduler job runs every 60 seconds to query active lessons and issue fresh tokens.

The main technical considerations are: (1) paho-mqtt v2 requires the new `CallbackAPIVersion.VERSION2` API with updated callback signatures, (2) MQTT callbacks run in a separate thread so each must create its own SQLAlchemy session (not share FastAPI's request-scoped session), (3) APScheduler's `BackgroundScheduler` is the correct choice since the MQTT client already uses a background thread and the scheduler jobs are synchronous DB operations.

**Primary recommendation:** Use paho-mqtt v2 `CallbackAPIVersion.VERSION2` with `loop_start()` threaded loop, APScheduler `BackgroundScheduler` with 60-second `IntervalTrigger`, both started/stopped in FastAPI's lifespan context manager. Each MQTT callback and scheduler job creates its own `SessionLocal()` with try/finally close.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Mixed payload format -- JSON for registration (`devices/register` with `{"device_id": "e101"}`), plain text for heartbeat/lux
- **D-02:** QoS 0 for heartbeats and lux, QoS 1 for token delivery (`attendance/device/{device_id}`)
- **D-03:** Registration contains device_id only; admin assigns room manually
- **D-04:** New token every scheduler tick; previous active token deactivated before new one created
- **D-05:** Tokens issued only during lesson window (between start_time and end_time)
- **D-06:** Scheduler issues tokens for enabled devices regardless of online status (is_enabled=True is the only gate)
- **D-07:** Heartbeat timeout: 90 seconds; device marked is_online=False if last_seen exceeds threshold
- **D-08:** Offline detection runs as separate background task (dedicated heartbeat monitor)
- **D-09:** MQTT client and APScheduler started in FastAPI lifespan. MQTT logic in `app/services/mqtt.py`, scheduler in `app/services/scheduler.py`
- **D-10:** paho-mqtt `loop_start()` threaded background loop, no async wrapper
- **D-11:** Each MQTT callback creates its own `SessionLocal()` DB session, commits, and closes
- **D-12:** Log new device registrations and errors; skip routine heartbeats/lux to stdout

### Claude's Discretion
- Internal structure of mqtt.py and scheduler.py (class-based vs functional)
- Exact APScheduler job configuration (IntervalTrigger vs CronTrigger)
- Error handling and reconnection strategy for MQTT client
- Token URL format details beyond `http://{SERVER_IP}/checkin?token={uuid}`
- Whether heartbeat monitor uses APScheduler or a simple asyncio task

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MQTT-01 | Server subscribes to `devices/register`, `devices/+/status`, `sensors/+/lux` | paho-mqtt v2 `subscribe()` with topic list, wildcard `+` supported |
| MQTT-02 | Registration message auto-creates device record with `is_enabled=False` | MQTT on_message callback + SessionLocal() + Device model create |
| MQTT-03 | Heartbeat message updates `is_online` and `last_seen` | on_message topic parsing + Device query by device_id |
| MQTT-04 | Sensor message updates `last_lux` | on_message topic parsing + Device query by device_id |
| MQTT-05 | `publish_token(device_id, url)` publishes to `attendance/device/{device_id}` | paho-mqtt v2 `publish()` with QoS 1 |
| MQTT-06 | Scheduler runs every minute and issues tokens for active, enabled schedule entries | APScheduler BackgroundScheduler + IntervalTrigger(minutes=1) |
| MQTT-07 | New token deactivates previous active token for that device | DB query: UPDATE is_active=False WHERE device_id AND is_active=True before INSERT |
| MQTT-08 | Token URL format: `http://{SERVER_IP}/checkin?token={uuid}` | Settings.server_ip + uuid4 |
| MQTT-09 | Token expires at lesson's end_time | datetime.combine(today, schedule_entry.end_time) for expires_at |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| paho-mqtt | 2.1.0 | MQTT client for Python | Official Eclipse Paho client, already pinned in requirements.txt |
| apscheduler | 3.11.2 | Background job scheduling | Standard Python scheduler, already pinned in requirements.txt |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| SQLAlchemy | 2.0.48 | DB access from MQTT callbacks and scheduler | Already in stack, used for all DB operations |
| uuid (stdlib) | -- | Token generation | `uuid.uuid4()` for unique token strings |
| json (stdlib) | -- | Parse registration payload | `json.loads()` for `devices/register` JSON messages |
| logging (stdlib) | -- | Structured logging for MQTT events | Filter routine vs important events per D-12 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| BackgroundScheduler | AsyncIOScheduler | AsyncIOScheduler would run in event loop, but MQTT callbacks are threaded anyway -- BackgroundScheduler is simpler and avoids mixing async/threaded patterns |
| IntervalTrigger | CronTrigger | CronTrigger gives cron-like syntax but IntervalTrigger(minutes=1) is simpler for "every minute" |
| loop_start() | asyncio-mqtt wrapper | Adds complexity for no benefit in this prototype -- D-10 locks this decision |

**Installation:**
```bash
# Already installed -- packages pinned in requirements.txt
pip install paho-mqtt==2.1.0 apscheduler==3.11.2
```

## Architecture Patterns

### Recommended Project Structure
```
app/
  services/
    __init__.py        # existing
    auth.py            # existing
    mqtt.py            # NEW: MQTT client, callbacks, publish_token
    scheduler.py       # NEW: APScheduler setup, token issuance job, heartbeat monitor job
  main.py              # MODIFIED: start/stop MQTT + scheduler in lifespan
```

### Pattern 1: paho-mqtt v2 Client with CallbackAPIVersion.VERSION2
**What:** paho-mqtt 2.x requires explicitly specifying the callback API version. VERSION2 has updated callback signatures.
**When to use:** Always -- VERSION1 is deprecated and will be removed in v3.
**Example:**
```python
# Source: https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html
import paho.mqtt.client as mqtt

def on_connect(client, userdata, connect_flags, reason_code, properties):
    if reason_code == 0:
        client.subscribe([
            ("devices/register", 0),
            ("devices/+/status", 0),
            ("sensors/+/lux", 0),
        ])

def on_message(client, userdata, message):
    topic = message.topic
    payload = message.payload.decode("utf-8")
    # Route by topic...

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect("mqtt", 1883, keepalive=60)
client.loop_start()  # Background thread
# ... on shutdown:
client.loop_stop()
client.disconnect()
```

### Pattern 2: Thread-safe DB Sessions in MQTT Callbacks (D-11)
**What:** Each MQTT callback creates its own DB session since callbacks run in paho's network thread, not in FastAPI's request lifecycle.
**When to use:** Every MQTT on_message handler that touches the database.
**Example:**
```python
from app.database import SessionLocal

def _handle_registration(payload: str):
    db = SessionLocal()
    try:
        # ... create/query Device ...
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

### Pattern 3: APScheduler BackgroundScheduler in FastAPI Lifespan
**What:** Start scheduler on app startup, shut down on app shutdown.
**When to use:** For the token issuance job and heartbeat monitor.
**Example:**
```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = BackgroundScheduler()

def issue_tokens():
    """Runs every 60 seconds. Creates own DB session."""
    db = SessionLocal()
    try:
        # Query active schedule entries for now
        # For each: deactivate old token, create new token, publish via MQTT
        db.commit()
    finally:
        db.close()

scheduler.add_job(issue_tokens, IntervalTrigger(minutes=1), id="issue_tokens")
scheduler.start()
# ... on shutdown:
scheduler.shutdown(wait=False)
```

### Pattern 4: Topic Routing in on_message
**What:** Parse MQTT topic to route to appropriate handler.
**When to use:** Single on_message callback dispatching to multiple handlers.
**Example:**
```python
def on_message(client, userdata, message):
    topic = message.topic
    payload = message.payload.decode("utf-8")

    if topic == "devices/register":
        _handle_registration(payload)
    elif topic.startswith("devices/") and topic.endswith("/status"):
        device_id = topic.split("/")[1]
        _handle_heartbeat(device_id, payload)
    elif topic.startswith("sensors/") and topic.endswith("/lux"):
        device_id = topic.split("/")[1]
        _handle_lux(device_id, payload)
```

### Pattern 5: Token Deactivation Before New Issuance (D-04)
**What:** Before creating a new token for a device, deactivate any existing active tokens.
**When to use:** Every scheduler tick when issuing a new token.
**Example:**
```python
from app.models.attendance_token import AttendanceToken
import uuid
from datetime import datetime, date

def _issue_token_for_device(db, device, schedule_entry, mqtt_client, server_ip):
    # Deactivate previous active tokens for this device
    db.query(AttendanceToken).filter(
        AttendanceToken.device_id == device.id,
        AttendanceToken.is_active == True,
    ).update({"is_active": False})

    # Create new token
    token_str = str(uuid.uuid4())
    token = AttendanceToken(
        token=token_str,
        device_id=device.id,
        schedule_entry_id=schedule_entry.id,
        lesson_date=date.today(),
        is_active=True,
        created_at=datetime.now(),
        expires_at=datetime.combine(date.today(), schedule_entry.end_time),
    )
    db.add(token)
    db.commit()

    # Publish to MQTT
    url = f"http://{server_ip}/checkin?token={token_str}"
    mqtt_client.publish(
        f"attendance/device/{device.device_id}",
        payload=url,
        qos=1,
    )
```

### Anti-Patterns to Avoid
- **Sharing FastAPI's request session in MQTT callbacks:** MQTT callbacks run in paho's thread, not in a request context. Always create a fresh `SessionLocal()`.
- **Using AsyncIOScheduler with synchronous DB calls:** The scheduler jobs do synchronous SQLAlchemy operations. BackgroundScheduler runs them in its own thread pool, avoiding blocking the event loop.
- **Forgetting CallbackAPIVersion:** paho-mqtt v2 will raise DeprecationWarning (or error) without `CallbackAPIVersion.VERSION2`.
- **Not subscribing in on_connect:** If the broker restarts, the client reconnects and on_connect fires again. Subscribing there ensures resubscription after reconnect.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MQTT topic parsing | Custom regex parser | Simple `str.split("/")` with pattern matching | Topics are simple 2-3 segment paths; split is sufficient |
| Scheduled job execution | Custom asyncio.sleep loop | APScheduler BackgroundScheduler | Handles missed executions, thread safety, shutdown gracefully |
| MQTT reconnection | Manual reconnect logic | paho-mqtt built-in reconnect (`reconnect_delay_set()`) | paho handles reconnection automatically when using `loop_start()` |
| Token UUID generation | Custom ID scheme | `uuid.uuid4()` | Standard, collision-proof, already used in Phase 5 |

**Key insight:** paho-mqtt's threaded loop and APScheduler's BackgroundScheduler handle all the concurrency complexity. Don't introduce asyncio wrappers or custom threading.

## Common Pitfalls

### Pitfall 1: paho-mqtt v2 Callback Signature Mismatch
**What goes wrong:** Using old v1 callback signatures (`def on_connect(client, userdata, flags, rc)`) causes runtime errors or silent failures with v2 API.
**Why it happens:** Most online examples still show v1 signatures. paho-mqtt 2.x changed `flags` to `connect_flags`, `rc` to `reason_code`, and added `properties`.
**How to avoid:** Always use `CallbackAPIVersion.VERSION2` and the 5-argument `on_connect(client, userdata, connect_flags, reason_code, properties)`.
**Warning signs:** DeprecationWarning about "Callback API version 1", unexpected callback argument errors.

### Pitfall 2: SQLite Thread Safety in MQTT Callbacks
**What goes wrong:** "SQLite objects created in a thread can only be used in that same thread" errors.
**Why it happens:** MQTT callbacks run in paho's network thread. If you try to reuse a session from another thread, SQLite raises.
**How to avoid:** The engine already has `check_same_thread=False`. Each callback creates a fresh `SessionLocal()` and closes it in finally block. This is safe because `check_same_thread=False` is set in `database.py`.
**Warning signs:** ProgrammingError about SQLite thread usage.

### Pitfall 3: Scheduler Job Overlapping
**What goes wrong:** If a scheduler job takes longer than 60 seconds (unlikely but possible with slow DB), the next tick starts while the previous is still running.
**Why it happens:** APScheduler by default allows concurrent execution of the same job.
**How to avoid:** Set `max_instances=1` on the job to prevent overlap. APScheduler will skip the tick if the previous run hasn't finished.
**Warning signs:** Duplicate token creation, DB lock contention.

### Pitfall 4: Token Expiry Timezone Issues
**What goes wrong:** `datetime.combine(date.today(), schedule_entry.end_time)` may produce unexpected results if server timezone differs from local school time.
**Why it happens:** Python `datetime.now()` and `date.today()` use system local time. SQLite stores naive datetimes.
**How to avoid:** Keep everything naive (no timezone) and ensure the Raspberry Pi system clock matches school timezone. This is the existing pattern in the codebase.
**Warning signs:** Tokens expiring at wrong times.

### Pitfall 5: on_connect Not Resubscribing After Broker Restart
**What goes wrong:** If the Mosquitto broker restarts, the MQTT client reconnects but loses its subscriptions.
**Why it happens:** MQTT subscriptions are session-based. Unless using persistent sessions (clean_session=False), subscriptions are lost on reconnect.
**How to avoid:** Always subscribe inside `on_connect` callback, not just at startup. This way, every reconnection triggers resubscription.
**Warning signs:** Device messages stop being processed after broker restart.

### Pitfall 6: Not Handling Missing Device in Heartbeat/Lux
**What goes wrong:** A device sends heartbeat/lux before registering, and the DB query returns None.
**Why it happens:** Race condition or misconfigured device.
**How to avoid:** Check if device exists in DB before updating. Log a warning if device_id not found. Optionally auto-create (but D-03 says registration creates device, so just log and skip).
**Warning signs:** NoneType attribute errors in callbacks.

## Code Examples

### MQTT Service Module Structure
```python
# app/services/mqtt.py
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
    if reason_code == 0:
        logger.info("Connected to MQTT broker")
        client.subscribe([
            ("devices/register", 0),
            ("devices/+/status", 0),
            ("sensors/+/lux", 0),
        ])
    else:
        logger.error("MQTT connection failed: %s", reason_code)

def _on_message(client, userdata, message):
    topic = message.topic
    payload = message.payload.decode("utf-8", errors="replace")
    try:
        if topic == "devices/register":
            _handle_register(payload)
        elif "/status" in topic:
            device_id = topic.split("/")[1]
            _handle_heartbeat(device_id, payload)
        elif "/lux" in topic:
            device_id = topic.split("/")[1]
            _handle_lux(device_id, payload)
    except Exception:
        logger.exception("Error processing MQTT message on %s", topic)

def _handle_register(payload: str):
    try:
        data = json.loads(payload)
        device_id = data["device_id"]
    except (json.JSONDecodeError, KeyError):
        device_id = payload.strip()
    db = SessionLocal()
    try:
        existing = db.query(Device).filter(Device.device_id == device_id).first()
        if existing:
            return
        device = Device(device_id=device_id, is_enabled=False, is_online=False)
        db.add(device)
        db.commit()
        logger.info("New device registered: %s", device_id)
    except Exception:
        db.rollback()
        logger.exception("Failed to register device %s", device_id)
    finally:
        db.close()

def _handle_heartbeat(device_id: str, payload: str):
    db = SessionLocal()
    try:
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if not device:
            return
        device.is_online = True
        device.last_seen = datetime.now()
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

def _handle_lux(device_id: str, payload: str):
    db = SessionLocal()
    try:
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if not device:
            return
        device.last_lux = float(payload)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

def publish_token(device_id: str, url: str):
    if _client and _client.is_connected():
        _client.publish(f"attendance/device/{device_id}", payload=url, qos=1)

def start_mqtt():
    global _client
    settings = get_settings()
    _client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    _client.on_connect = _on_connect
    _client.on_message = _on_message
    _client.connect(settings.mqtt_broker, settings.mqtt_port, keepalive=60)
    _client.loop_start()

def stop_mqtt():
    global _client
    if _client:
        _client.loop_stop()
        _client.disconnect()
        _client = None
```

### Scheduler Service Module Structure
```python
# app/services/scheduler.py
import logging
import uuid
from datetime import datetime, date
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.config import get_settings
from app.database import SessionLocal
from app.models.device import Device
from app.models.schedule_entry import ScheduleEntry
from app.models.attendance_token import AttendanceToken
from app.services.mqtt import publish_token

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None

def _issue_tokens():
    now = datetime.now()
    today = date.today()
    current_time = now.time()
    weekday = today.weekday()

    db = SessionLocal()
    try:
        entries = db.query(ScheduleEntry).join(Device).filter(
            ScheduleEntry.weekday == weekday,
            ScheduleEntry.start_time <= current_time,
            ScheduleEntry.end_time > current_time,
            Device.is_enabled == True,
        ).all()

        settings = get_settings()
        for entry in entries:
            device = db.query(Device).get(entry.device_id)
            if not device:
                continue

            # Deactivate previous active tokens for this device
            db.query(AttendanceToken).filter(
                AttendanceToken.device_id == device.id,
                AttendanceToken.is_active == True,
            ).update({"is_active": False})

            # Create new token
            token_str = str(uuid.uuid4())
            token = AttendanceToken(
                token=token_str,
                device_id=device.id,
                schedule_entry_id=entry.id,
                lesson_date=today,
                is_active=True,
                created_at=now,
                expires_at=datetime.combine(today, entry.end_time),
            )
            db.add(token)
            db.commit()

            # Publish token URL
            url = f"http://{settings.server_ip}/checkin?token={token_str}"
            publish_token(device.device_id, url)
    except Exception:
        db.rollback()
        logger.exception("Error in token issuance job")
    finally:
        db.close()

def _check_heartbeats():
    """Mark devices offline if last_seen > 90 seconds ago."""
    from datetime import timedelta
    threshold = datetime.now() - timedelta(seconds=90)
    db = SessionLocal()
    try:
        db.query(Device).filter(
            Device.is_online == True,
            Device.last_seen < threshold,
        ).update({"is_online": False})
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

def start_scheduler():
    global _scheduler
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _issue_tokens,
        IntervalTrigger(minutes=1),
        id="issue_tokens",
        max_instances=1,
    )
    _scheduler.add_job(
        _check_heartbeats,
        IntervalTrigger(seconds=30),
        id="check_heartbeats",
        max_instances=1,
    )
    _scheduler.start()

def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
```

### Lifespan Integration
```python
# In app/main.py lifespan()
from app.services.mqtt import start_mqtt, stop_mqtt
from app.services.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        await _seed_admin(db)
    finally:
        db.close()

    start_mqtt()
    start_scheduler()
    yield
    stop_scheduler()
    stop_mqtt()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| paho-mqtt v1 callbacks (`flags`, `rc`) | paho-mqtt v2 (`connect_flags`, `reason_code`, `properties`) | paho-mqtt 2.0 (Feb 2024) | Must use `CallbackAPIVersion.VERSION2` |
| APScheduler 4.x (alpha, async-only) | APScheduler 3.x (stable, sync+async) | 3.11.2 is latest stable | Stick with 3.x -- 4.x is alpha and incompatible |
| `client = mqtt.Client()` | `client = mqtt.Client(callback_api_version=...)` | paho-mqtt 2.0 | First positional arg is now callback_api_version |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 |
| Config file | none (default discovery) |
| Quick run command | `python -m pytest tests/ -x -q` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MQTT-01 | Server subscribes to 3 topic patterns | unit (mock client) | `python -m pytest tests/test_mqtt.py::test_subscribe_topics -x` | No -- Wave 0 |
| MQTT-02 | Registration creates device with is_enabled=False | unit | `python -m pytest tests/test_mqtt.py::test_register_device -x` | No -- Wave 0 |
| MQTT-03 | Heartbeat updates is_online and last_seen | unit | `python -m pytest tests/test_mqtt.py::test_heartbeat_update -x` | No -- Wave 0 |
| MQTT-04 | Lux message updates last_lux | unit | `python -m pytest tests/test_mqtt.py::test_lux_update -x` | No -- Wave 0 |
| MQTT-05 | publish_token publishes to correct topic | unit (mock client) | `python -m pytest tests/test_mqtt.py::test_publish_token -x` | No -- Wave 0 |
| MQTT-06 | Scheduler issues tokens for active lessons | unit | `python -m pytest tests/test_scheduler.py::test_issue_tokens -x` | No -- Wave 0 |
| MQTT-07 | New token deactivates previous active token | unit | `python -m pytest tests/test_scheduler.py::test_deactivate_previous_token -x` | No -- Wave 0 |
| MQTT-08 | Token URL format matches spec | unit | `python -m pytest tests/test_scheduler.py::test_token_url_format -x` | No -- Wave 0 |
| MQTT-09 | Token expires_at matches lesson end_time | unit | `python -m pytest tests/test_scheduler.py::test_token_expiry -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_mqtt.py` -- covers MQTT-01 through MQTT-05 (mock paho client, test handler functions directly)
- [ ] `tests/test_scheduler.py` -- covers MQTT-06 through MQTT-09 (mock MQTT publish, test scheduler job with real DB session)

### Testing Strategy Notes
- **MQTT callbacks are testable without a broker:** Extract handler functions (`_handle_register`, `_handle_heartbeat`, `_handle_lux`) and test them directly with a DB session. Mock the paho client for publish verification.
- **Scheduler job is testable without APScheduler:** Call `_issue_tokens()` directly with mocked `datetime.now()` and verify DB state + mock publish calls.
- **No integration test with real Mosquitto needed:** Unit tests with mocks are sufficient for this phase. Docker Compose integration testing happens at deployment time.

## Open Questions

1. **Heartbeat monitor frequency**
   - What we know: D-08 says dedicated background task, D-07 says 90-second timeout
   - Recommendation: Run every 30 seconds via APScheduler (checks twice per timeout window). This is Claude's discretion per CONTEXT.md.

2. **MQTT reconnection behavior**
   - What we know: paho-mqtt `loop_start()` handles reconnection automatically
   - Recommendation: Use `reconnect_delay_set(min_delay=1, max_delay=30)` for exponential backoff. Log reconnection events.

## Project Constraints (from CLAUDE.md)

- **Tech Stack:** FastAPI + Jinja2 + SQLAlchemy + SQLite + Mosquitto + paho-mqtt + APScheduler (all confirmed)
- **Hardware:** No ESP32 -- dummy clients only (Phase 7, out of scope here)
- **Database:** SQLite with `check_same_thread=False` already configured
- **Runtime:** Raspberry Pi ARM -- all dependencies are pure Python or have ARM wheels
- **CSS:** Pico CSS (no UI changes in this phase)

## Sources

### Primary (HIGH confidence)
- [paho-mqtt v2 official docs](https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html) - Client API, callback signatures, connect/subscribe/publish
- [paho-mqtt migration guide](https://eclipse.dev/paho/files/paho.mqtt.python/html/migrations.html) - v1 to v2 API changes
- [APScheduler 3.x user guide](https://apscheduler.readthedocs.io/en/3.x/userguide.html) - BackgroundScheduler, triggers

### Secondary (MEDIUM confidence)
- [paho-mqtt PyPI](https://pypi.org/project/paho-mqtt/) - Version 2.1.0 confirmed as latest
- [APScheduler PyPI](https://pypi.org/project/APScheduler/) - Version 3.11.2 confirmed as latest stable
- Existing codebase patterns (database.py, main.py lifespan, conftest.py) - Verified by reading source

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - packages already pinned, versions verified against PyPI
- Architecture: HIGH - decisions locked in CONTEXT.md, patterns verified against official docs
- Pitfalls: HIGH - paho-mqtt v2 migration is well-documented, SQLite threading is a known concern already handled in codebase

**Research date:** 2026-03-30
**Valid until:** 2026-04-30 (stable libraries, no breaking changes expected)
