# Phase 6: MQTT & Scheduler - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

The server issues time-limited tokens to devices on a schedule and tracks device state via MQTT. Server subscribes to device registration, heartbeat, and lux sensor topics. A scheduler runs every minute and publishes token URLs to active, enabled devices with current lessons. Previous tokens are deactivated when new ones are issued. Tokens expire at lesson end_time.

</domain>

<decisions>
## Implementation Decisions

### MQTT Topic Contract
- **D-01:** Mixed payload format — JSON for registration (`devices/register` with `{"device_id": "e101"}`), plain text for simple values (heartbeat status, lux readings).
- **D-02:** QoS 0 for heartbeats (`devices/+/status`) and sensor data (`sensors/+/lux`). QoS 1 for token delivery (`attendance/device/{device_id}`) to ensure devices receive the check-in URL.
- **D-03:** Registration message contains `device_id` only (plain text or minimal JSON). Admin assigns room manually via the admin UI after registration.

### Scheduler Behavior
- **D-04:** New token issued every scheduler tick (every minute) for each active lesson+device combination. Previous active token for that device is deactivated before the new one is created.
- **D-05:** Tokens issued only during the lesson window (current time between `start_time` and `end_time`). No pre-issuing before lesson starts.
- **D-06:** Scheduler issues tokens for enabled devices regardless of online status (`is_enabled=True` is the only gate). Token is ready if device reconnects.

### Device Lifecycle
- **D-07:** Heartbeat timeout: 90 seconds. If `last_seen` is older than 90 seconds, device is marked `is_online=False`.
- **D-08:** Offline detection runs as a separate background task (dedicated heartbeat monitor), not piggybacked on the scheduler loop.

### MQTT Integration Architecture
- **D-09:** MQTT client and APScheduler started in FastAPI's lifespan context manager. MQTT logic in `app/services/mqtt.py`, scheduler logic in `app/services/scheduler.py`.
- **D-10:** paho-mqtt's `loop_start()` threaded background loop. No async wrapper — keep it simple with the built-in thread.
- **D-11:** Each MQTT callback creates its own `SessionLocal()` DB session, commits, and closes. Independent of FastAPI's request-scoped sessions.
- **D-12:** Logging: log new device registrations and errors to stdout. Skip routine heartbeats and lux updates to avoid noise.

### Claude's Discretion
- Internal structure of mqtt.py and scheduler.py (class-based vs functional)
- Exact APScheduler job configuration (IntervalTrigger vs CronTrigger)
- Error handling and reconnection strategy for MQTT client
- Token URL format details beyond the required `http://{SERVER_IP}/checkin?token={uuid}`
- Whether heartbeat monitor uses APScheduler or a simple asyncio task

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements fully captured in decisions above and REQUIREMENTS.md (MQTT-01 through MQTT-09).

### Codebase References
- `app/config.py` — Settings with `mqtt_broker`, `mqtt_port`, `server_ip` already defined
- `app/models/device.py` — Device model with `device_id`, `room`, `is_enabled`, `is_online`, `last_seen`, `last_lux`
- `app/models/attendance_token.py` — AttendanceToken model with `token`, `device_id`, `schedule_entry_id`, `lesson_date`, `is_active`, `expires_at`
- `app/models/schedule_entry.py` — ScheduleEntry model with `device_id`, `teacher_id`, `class_name`, `weekday`, `start_time`, `end_time`
- `app/main.py` — FastAPI app with lifespan context manager (lines 34-43), where MQTT and scheduler should be integrated
- `app/database.py` — `SessionLocal` factory for creating DB sessions outside request scope
- `docker-compose.yml` — Mosquitto broker service already configured, dummy clients as stubs
- `mosquitto/config/mosquitto.conf` — Anonymous auth enabled, persistence on
- `requirements.txt` — `paho-mqtt==2.1.0` and `apscheduler==3.11.2` already pinned

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/config.py:Settings` — MQTT and server_ip settings already defined, just need to be consumed
- `app/database.py:SessionLocal` — Session factory already used in lifespan for admin seeding, same pattern for MQTT callbacks
- `app/models/` — All required models (Device, AttendanceToken, ScheduleEntry) already exist with correct fields

### Established Patterns
- Lifespan context manager in `main.py` handles startup/shutdown — MQTT client and scheduler should integrate here
- DB sessions created via `SessionLocal()` with try/finally close pattern (see `_seed_admin` in main.py)
- Router imports at bottom of main.py — service initialization should happen in lifespan, not at import time

### Integration Points
- `app/main.py:lifespan()` — Start MQTT client and scheduler on startup, stop on shutdown
- `app/services/mqtt.py` (new) — Subscribe to topics, handle incoming messages, publish tokens
- `app/services/scheduler.py` (new) — APScheduler job that queries active lessons and issues tokens
- Token creation reuses the AttendanceToken model pattern from Phase 5 check-in flow

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-mqtt-scheduler*
*Context gathered: 2026-03-30*
