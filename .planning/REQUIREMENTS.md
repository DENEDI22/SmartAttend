# Requirements: SmartAttend

**Defined:** 2026-04-02
**Core Value:** Students can check in to a lesson by tapping their phone on the classroom NFC device -- the entire flow from tap to attendance record must work reliably.

## v1.1 Requirements

Requirements for physical device integration. Each maps to roadmap phases.

### Network & Infrastructure

- [x] **NET-01**: Mosquitto broker listens on LAN interface so ESP32 devices can connect over WiFi
- [x] **NET-02**: Ngrok runs as a Docker Compose service, configured via `.env` (auth token + domain)
- [x] **NET-03**: Server reads ngrok public base URL from environment and uses it for all check-in token URLs

### Firmware

- [x] **FW-01**: ESP32 firmware publishes registration JSON to `devices/register` on MQTT connect
- [x] **FW-02**: ESP32 firmware publishes heartbeat to `devices/{device_id}/status` every 30 seconds
- [x] **FW-03**: ESP32 firmware subscribes to `attendance/device/{device_id}` and writes received URL to NFC tag
- [x] **FW-04**: ESP32 lights LED on GPIO 13 when MQTT is connected, turns off when disconnected

### Cleanup

- [x] **CLN-01**: Dummy client containers removed from Docker Compose (one kept commented out for dev use)

## Future Requirements

### Firmware -- Deferred

- **FW-LUX**: ESP32 firmware publishes lux reading to `sensors/{device_id}/lux` every 60 seconds (sensor not connected yet)

### Security -- Deferred

- **SEC-01**: MQTT password-based authentication for production hardening

## Out of Scope

| Feature | Reason |
|---------|--------|
| Moodle API integration | Attendance stored locally; Moodle write is future work |
| RPi hardware power management | Out of scope for prototype |
| Student NFC card check-in (UID) | Requires firmware support beyond current scope |
| OAuth / SSO login | Username/password sufficient for school prototype |
| Lux sensor readings | Hardware sensor not connected yet -- deferred to future milestone |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| NET-01 | Phase 8 | Complete |
| NET-02 | Phase 8 | Complete |
| NET-03 | Phase 8 | Complete |
| CLN-01 | Phase 8 | Complete |
| FW-01 | Phase 9 | Complete |
| FW-02 | Phase 9 | Complete |
| FW-03 | Phase 9 | Complete |
| FW-04 | Phase 9 | Complete |

**Coverage:**
- v1.1 requirements: 8 total
- Mapped to phases: 8
- Unmapped: 0

---
*Requirements defined: 2026-04-02*
*Last updated: 2026-04-02 after roadmap revision*
