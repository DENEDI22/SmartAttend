# Phase 6: MQTT & Scheduler - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-30
**Phase:** 06-mqtt-scheduler
**Areas discussed:** MQTT topic contract, Scheduler behavior, Device lifecycle, MQTT integration architecture

---

## MQTT Topic Contract

### Payload format

| Option | Description | Selected |
|--------|-------------|----------|
| JSON payloads | All messages use JSON. Structured, extensible, easy to validate. | |
| Plain text payloads | Simple strings. Minimal overhead, harder to extend. | |
| Mixed | JSON for registration (multiple fields), plain text for simple values like lux. | ✓ |

**User's choice:** Mixed
**Notes:** JSON for structured messages (registration), plain text for simple sensor values.

### QoS level

| Option | Description | Selected |
|--------|-------------|----------|
| QoS 0 everywhere | Fire-and-forget. Simplest, sufficient for prototype. | |
| QoS 1 for tokens | At-least-once for token delivery, QoS 0 for heartbeats/sensors. | ✓ |
| QoS 1 everywhere | At-least-once for all messages. | |

**User's choice:** QoS 1 for tokens
**Notes:** Ensures devices receive check-in URLs reliably, while keeping heartbeats lightweight.

### Registration payload

| Option | Description | Selected |
|--------|-------------|----------|
| device_id + room | JSON with both fields. Auto-populates room on creation. | |
| device_id only | Minimal payload. Admin assigns room manually via UI. | ✓ |
| You decide | Claude picks. | |

**User's choice:** device_id only
**Notes:** Admin assigns room after registration via the admin interface.

---

## Scheduler Behavior

### Token reuse vs new token

| Option | Description | Selected |
|--------|-------------|----------|
| Keep existing active token | Skip if valid token exists. Fewer DB writes. | |
| New token every minute | Deactivate old, issue fresh each cycle. | ✓ |
| You decide | Claude picks. | |

**User's choice:** New token every minute
**Notes:** Device always gets the latest URL. Previous token deactivated before new one created.

### Pre-issuing tokens

| Option | Description | Selected |
|--------|-------------|----------|
| Only during lesson | Token issued only when current time is between start_time and end_time. | ✓ |
| Pre-issue 5 min early | Issue starting 5 minutes before start_time. | |
| You decide | Claude picks. | |

**User's choice:** Only during lesson
**Notes:** Simple logic, no early check-ins.

### Offline device handling

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, issue anyway | Scheduler checks is_enabled only. Token ready if device reconnects. | ✓ |
| No, skip offline devices | Only issue for enabled AND online devices. | |
| You decide | Claude picks. | |

**User's choice:** Yes, issue anyway
**Notes:** is_enabled is the only gate. Simplifies logic and handles reconnection gracefully.

---

## Device Lifecycle

### Heartbeat timeout

| Option | Description | Selected |
|--------|-------------|----------|
| 90 seconds | 3 missed heartbeats. Quick detection, reasonable tolerance. | ✓ |
| 60 seconds | 2 missed heartbeats. Aggressive. | |
| 2 minutes | 4 missed heartbeats. More tolerant. | |
| You decide | Claude picks. | |

**User's choice:** 90 seconds
**Notes:** None.

### Offline detection mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| Scheduler checks staleness | Piggyback on existing 1-minute scheduler loop. | |
| Separate background task | Dedicated heartbeat monitor on its own interval. | ✓ |
| You decide | Claude picks. | |

**User's choice:** Separate background task
**Notes:** More responsive offline detection, independent of scheduler timing.

---

## MQTT Integration Architecture

### Where MQTT client and scheduler live

| Option | Description | Selected |
|--------|-------------|----------|
| Lifespan hook + service module | Start in FastAPI lifespan. mqtt.py + scheduler.py in services/. | ✓ |
| Standalone background thread | Separate thread started at import time. | |
| You decide | Claude picks. | |

**User's choice:** Lifespan hook + service module
**Notes:** Clean separation, proper startup/shutdown lifecycle.

### MQTT loop style

| Option | Description | Selected |
|--------|-------------|----------|
| loop_start() threaded | paho-mqtt's built-in background thread. | ✓ |
| Async wrapper (aiomqtt) | asyncio-compatible client, more idiomatic with FastAPI. | |
| You decide | Claude picks. | |

**User's choice:** loop_start() threaded
**Notes:** Simple, well-tested. No extra dependency.

### DB session strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Own SessionLocal() per callback | Fresh session per message handler. Independent of request scope. | ✓ |
| Shared session with locking | One long-lived session with thread locks. | |
| You decide | Claude picks. | |

**User's choice:** Own SessionLocal() per callback
**Notes:** Matches existing pattern from lifespan admin seeding.

### Logging level

| Option | Description | Selected |
|--------|-------------|----------|
| Registrations + errors only | Log new devices and errors. Skip routine messages. | ✓ |
| Log everything | All MQTT messages including heartbeats and lux. | |
| You decide | Claude picks. | |

**User's choice:** Registrations + errors only
**Notes:** Avoid noise from frequent heartbeats and lux updates.

---

## Claude's Discretion

- Internal structure of mqtt.py and scheduler.py (class-based vs functional)
- Exact APScheduler job configuration
- Error handling and reconnection for MQTT client
- Token URL format details
- Whether heartbeat monitor uses APScheduler or asyncio task
