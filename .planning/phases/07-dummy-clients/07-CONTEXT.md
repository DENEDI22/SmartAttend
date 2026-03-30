# Phase 7: Dummy Clients - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Three Python containers faithfully simulate ESP32 MQTT clients so the full flow can be tested without hardware. Each client publishes registration, heartbeat, and lux messages, and subscribes to receive token URLs. The MQTT topic contract is locked from Phase 6. Docker Compose already defines the 3 client containers with environment variables.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
User chose "You decide on all" — Claude has full flexibility on all implementation decisions for this phase. The MQTT contract from Phase 6 is the binding spec:

**Locked from Phase 6 (not negotiable):**
- Registration: publish to `devices/register` with JSON `{"device_id": "<id>"}` or plain device_id
- Heartbeat: publish to `devices/{device_id}/status` every 30 seconds, QoS 0
- Lux: publish to `sensors/{device_id}/lux` every 60 seconds with configurable value, QoS 0
- Token subscription: subscribe to `attendance/device/{device_id}`, QoS 1
- Environment variables: `DEVICE_ID`, `ROOM`, `MQTT_BROKER`, `MQTT_PORT`, `LUX_VALUE`

**Claude decides:**
- Client startup logging format and content
- Heartbeat payload content (e.g., "online", "1", or timestamp)
- Lux value: exact configurable value or slight randomization around LUX_VALUE
- Token URL printing format (stdout, with timestamp, etc.)
- Reconnection and resilience strategy (broker down at startup, reconnect behavior)
- Graceful shutdown handling (SIGTERM)
- Dockerfile changes (add paho-mqtt dependency, keep image slim)
- Whether to use paho-mqtt v2 API (matching server) or simpler v1 style
- Internal code structure (threading, scheduling approach for periodic publishes)
- Whether to add a separate requirements.txt for dummy_client or install inline

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements fully captured in Phase 6 MQTT contract and REQUIREMENTS.md (DUMMY-01 through DUMMY-07).

### Codebase References
- `app/services/mqtt.py` — Server-side MQTT handlers (the contract the dummy clients must satisfy)
- `dummy_client/main.py` — Current Phase 1 stub (to be replaced)
- `dummy_client/Dockerfile` — Existing Dockerfile (needs paho-mqtt added)
- `docker-compose.yml` — Already defines client-e101, client-e102, client-e103 with env vars
- `.planning/phases/06-mqtt-scheduler/06-CONTEXT.md` — Phase 6 decisions (D-01 through D-03 define topic contract)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `dummy_client/main.py` — Stub that reads DEVICE_ID and ROOM from env. Will be completely rewritten.
- `dummy_client/Dockerfile` — Minimal Python 3.11-slim image. Needs paho-mqtt dependency added.
- `docker-compose.yml` — All 3 client containers already configured with correct env vars (DEVICE_ID, ROOM, MQTT_BROKER, MQTT_PORT, LUX_VALUE).

### Established Patterns
- Server uses paho-mqtt v2 API (`CallbackAPIVersion.VERSION2`) — dummy clients should match for consistency
- Server subscribes in `on_connect` callback for auto-resubscription on reconnect — same pattern applies to clients
- Plain text payloads for heartbeat/lux, JSON for registration (Phase 6 D-01)

### Integration Points
- Dummy client publishes to topics the server subscribes to (`devices/register`, `devices/+/status`, `sensors/+/lux`)
- Dummy client subscribes to `attendance/device/{device_id}` where the server's scheduler publishes token URLs
- `paho-mqtt==2.1.0` already in main `requirements.txt` — dummy client needs its own copy or inline pip install

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. User deferred all decisions to Claude.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 07-dummy-clients*
*Context gathered: 2026-03-30*
