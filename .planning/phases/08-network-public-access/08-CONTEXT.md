# Phase 8: Network & Public Access - Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Make the SmartAttend server reachable from the internet via ngrok, generate check-in URLs using the ngrok public domain, expose Mosquitto on the LAN for ESP32 WiFi connections, and clean up Docker Compose by removing dummy client services.

</domain>

<decisions>
## Implementation Decisions

### Token URL Configuration
- **D-01:** Replace `SERVER_IP` env var with `BASE_URL` (e.g., `https://myapp.ngrok-free.app`). `SERVER_IP` is removed entirely.
- **D-02:** Token URL format becomes `{BASE_URL}/checkin?token={token}` — scheme is included in `BASE_URL`, no hardcoded `http://`.
- **D-03:** Update `app/config.py` Settings class: remove `server_ip`, add `base_url`.
- **D-04:** Update `app/services/scheduler.py` line 77 to use `settings.base_url`.
- **D-05:** Update `.env.example` and `.env` — replace `SERVER_IP=localhost` with `BASE_URL=http://localhost:8000` (dev default).

### Ngrok Container
- **D-06:** Use official `ngrok/ngrok` Docker image in docker-compose.yml.
- **D-07:** Auth token and fixed domain configured via `.env` (`NGROK_AUTHTOKEN`, `NGROK_DOMAIN`).
- **D-08:** Ngrok tunnels directly to `server:8000` — no reverse proxy.
- **D-09:** Fixed/reserved ngrok domain — `BASE_URL` is stable across restarts.

### Mosquitto LAN Access
- **D-10:** Current setup already works — `ports: "1883:1883"` exposes MQTT on host. Standard network, no firewall changes needed.
- **D-11:** ESP32 devices connect to `<RPi-IP>:1883` over WiFi. No config changes to mosquitto.conf required.

### Docker Compose Cleanup
- **D-12:** Remove all 3 dummy client services (`client-e101`, `client-e102`, `client-e103`).
- **D-13:** Keep one dummy client service commented out in docker-compose.yml for development/testing use.

### Claude's Discretion
- Ngrok container command/entrypoint configuration details
- Whether to add health checks for the ngrok container
- Exact ngrok config file format vs CLI args approach

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Token URL generation
- `app/services/scheduler.py` — Line 77: current URL generation (`http://{settings.server_ip}/checkin?token=...`), must be updated
- `app/config.py` — Settings class with `server_ip` field, must be replaced with `base_url`

### Environment configuration
- `.env.example` — Reference for all env vars, must be updated
- `.env` — Active config, must be updated

### Docker infrastructure
- `docker-compose.yml` — Current service definitions (server, mqtt, 3 dummy clients), must add ngrok and remove dummy clients
- `mosquitto/config/mosquitto.conf` — MQTT broker config, no changes needed

### Existing MQTT contract (firmware reference)
- `dummy_client/main.py` — Current MQTT contract implementation (topics, message formats)
- `app/services/mqtt.py` — Server-side MQTT handlers
- `ESP32THINGS/POC-Code/ESP32.ino` — POC firmware for reference (Phase 9 scope)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/config.py:Settings` — pydantic-settings class, env var loading via `SettingsConfigDict`. Adding `base_url` field follows existing pattern.
- `docker-compose.yml` — Well-structured Compose file, easy to add ngrok service and remove dummy clients.

### Established Patterns
- Environment variables loaded via pydantic-settings with `.env` file
- All services use `restart: unless-stopped`
- Services reference each other by Docker Compose service name (e.g., `mqtt` for MQTT broker)
- `depends_on` used for service ordering

### Integration Points
- `app/services/scheduler.py:77` — Token URL generation, only place `server_ip` is used for URL construction
- `tests/conftest.py:31` — Tests set `SERVER_IP=127.0.0.1`, will need updating to `BASE_URL`
- `tests/test_foundation.py:85` — Tests check for required env vars including `SERVER_IP`, needs update
- `tests/test_scheduler.py:201` — Token URL format test, needs update

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

*Phase: 08-network-public-access*
*Context gathered: 2026-04-02*
