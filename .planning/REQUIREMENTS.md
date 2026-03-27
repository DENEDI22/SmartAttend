# Requirements: SmartAttend

**Defined:** 2026-03-27
**Core Value:** Students can check in to a lesson by tapping their phone on the classroom NFC device — the entire flow from tap to attendance record must work reliably.

## v1 Requirements

### Foundation

- [x] **FOUND-01**: Project directory structure matches specification (models/, routers/, services/, templates/, static/)
- [x] **FOUND-02**: `config.py` loads all settings from `.env` via pydantic-settings
- [x] **FOUND-03**: `database.py` provides SQLAlchemy engine, session factory, and `Base`
- [ ] **FOUND-04**: All 5 models exist: User, Device (with `is_enabled`), ScheduleEntry, AttendanceToken, AttendanceRecord
- [ ] **FOUND-05**: `docker-compose.yml` starts server + mqtt + 3 dummy client stubs cleanly
- [ ] **FOUND-06**: `Dockerfile` builds a multi-arch image (linux/arm64, linux/arm/v7)
- [ ] **FOUND-07**: `mosquitto/config/mosquitto.conf` is present and correct
- [ ] **FOUND-08**: `.env.example` documents all required environment variables

### Authentication

- [ ] **AUTH-01**: User can log in with username and password via POST `/auth/login`
- [ ] **AUTH-02**: Server sets an HTTP-only JWT cookie on successful login
- [ ] **AUTH-03**: JWT expires after 8 hours for admin/teacher, 1 hour for students
- [ ] **AUTH-04**: User can log out via POST `/auth/logout` (cookie cleared)
- [ ] **AUTH-05**: GET `/auth/me` returns current user info for authenticated users
- [ ] **AUTH-06**: `require_role(*roles)` dependency rejects wrong roles with 403
- [ ] **AUTH-07**: Login page (`/login`) renders and submits correctly

### Admin

- [ ] **ADMIN-01**: Admin can view all registered devices with status (online/offline, enabled/disabled, last seen, last lux)
- [ ] **ADMIN-02**: Admin can assign a device to a room and give it a label
- [ ] **ADMIN-03**: Admin can enable/disable a device (controls token issuance)
- [ ] **ADMIN-04**: Admin can view all users (name, role, class)
- [ ] **ADMIN-05**: Admin can create a new user (name, username, password, role, class)
- [ ] **ADMIN-06**: Admin can deactivate a user (soft delete — records preserved)
- [ ] **ADMIN-07**: Admin can view the full timetable across all devices
- [ ] **ADMIN-08**: Admin can add a schedule entry (device, teacher, class, subject, weekday, start/end time)
- [ ] **ADMIN-09**: Admin cannot add a conflicting schedule entry (same device + overlapping time = rejected)
- [ ] **ADMIN-10**: Admin can delete a schedule entry

### Teacher

- [ ] **TEACH-01**: Teacher can view today's lessons on their dashboard
- [ ] **TEACH-02**: Each lesson on the dashboard shows checked-in count vs expected student count
- [ ] **TEACH-03**: Teacher can view the full attendance list for a specific lesson
- [ ] **TEACH-04**: Teacher can export attendance for a lesson as CSV

### Student Check-in

- [ ] **CHKIN-01**: GET `/checkin?token=<uuid>` renders a page showing lesson info (subject, teacher, room)
- [ ] **CHKIN-02**: Page shows a login form (or uses existing session cookie)
- [ ] **CHKIN-03**: POST `/checkin` validates token: exists, active, not expired
- [ ] **CHKIN-04**: POST `/checkin` rejects duplicate check-in for same student + lesson
- [ ] **CHKIN-05**: POST `/checkin` writes an AttendanceRecord on success and shows confirmation
- [ ] **CHKIN-06**: Expired token shows clear error message ("Diese Stunde ist bereits beendet")
- [ ] **CHKIN-07**: Invalid token shows appropriate error

### MQTT & Scheduler

- [ ] **MQTT-01**: Server subscribes to `devices/register`, `devices/+/status`, `sensors/+/lux`
- [ ] **MQTT-02**: Registration message auto-creates device record with `is_enabled=False`
- [ ] **MQTT-03**: Heartbeat message updates `is_online` and `last_seen` for the device
- [ ] **MQTT-04**: Sensor message updates `last_lux` for the device
- [ ] **MQTT-05**: `publish_token(device_id, url)` publishes to `attendance/device/{device_id}`
- [ ] **MQTT-06**: Scheduler runs every minute and issues tokens for active, enabled schedule entries
- [ ] **MQTT-07**: When a new token is issued for a device, previous active token is deactivated
- [ ] **MQTT-08**: Token URL format: `http://{SERVER_IP}/checkin?token={uuid}`
- [ ] **MQTT-09**: Token expires at the lesson's `end_time`

### Dummy Clients

- [ ] **DUMMY-01**: Dummy client publishes `devices/register` on startup
- [ ] **DUMMY-02**: Dummy client publishes `devices/{id}/status` heartbeat every 30 seconds
- [ ] **DUMMY-03**: Dummy client publishes `sensors/{id}/lux` every 60 seconds with configurable lux value
- [ ] **DUMMY-04**: Dummy client subscribes to `attendance/device/{id}` and prints received URL to console
- [ ] **DUMMY-05**: Each dummy client is fully configured via environment variables (DEVICE_ID, ROOM, MQTT_BROKER, MQTT_PORT, LUX_VALUE)
- [ ] **DUMMY-06**: `dummy_client/Dockerfile` exists and is included in `docker-compose.yml`
- [ ] **DUMMY-07**: Three dummy client instances run as separate containers (client-e101, client-e102, client-e103)

## v2 Requirements

### Security Hardening

- **SEC-01**: MQTT broker requires password-based authentication
- **SEC-02**: Admin can rotate the SECRET_KEY without losing all sessions
- **SEC-03**: Rate limiting on `/auth/login` endpoint

### Hardware Integration

- **HW-01**: ESP32 firmware implements same MQTT contract as dummy clients
- **HW-02**: Student NFC card (Schülerausweis UID) check-in without a web form
- **HW-03**: RPi hardware power management via GPIO + RTC module

### Integrations

- **INT-01**: Attendance records optionally written to Moodle REST API
- **INT-02**: Import users/classes from Moodle or CSV

## Out of Scope

| Feature | Reason |
|---------|--------|
| ESP32 firmware | No hardware available; dummy clients are the dev-time substitute |
| Moodle API integration | Prototype stores attendance locally; Moodle write is a future milestone |
| RPi GPIO/RTC power management | Hardware circuit required; out of scope for software prototype |
| Student NFC card (Schülerausweis) check-in | Requires ESP32 firmware; future extension |
| MQTT password auth | Anonymous allowed in prototype; production hardening is v2 |
| OAuth / SSO login | Username/password sufficient for school prototype |
| Real-time attendance updates (WebSocket) | Not needed; page refresh is sufficient for teacher dashboard |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOUND-01 | Phase 1 | Complete |
| FOUND-02 | Phase 1 | Complete |
| FOUND-03 | Phase 1 | Complete |
| FOUND-04 | Phase 1 | Pending |
| FOUND-05 | Phase 1 | Pending |
| FOUND-06 | Phase 1 | Pending |
| FOUND-07 | Phase 1 | Pending |
| FOUND-08 | Phase 1 | Pending |
| AUTH-01 | Phase 2 | Pending |
| AUTH-02 | Phase 2 | Pending |
| AUTH-03 | Phase 2 | Pending |
| AUTH-04 | Phase 2 | Pending |
| AUTH-05 | Phase 2 | Pending |
| AUTH-06 | Phase 2 | Pending |
| AUTH-07 | Phase 2 | Pending |
| ADMIN-01 | Phase 3 | Pending |
| ADMIN-02 | Phase 3 | Pending |
| ADMIN-03 | Phase 3 | Pending |
| ADMIN-04 | Phase 3 | Pending |
| ADMIN-05 | Phase 3 | Pending |
| ADMIN-06 | Phase 3 | Pending |
| ADMIN-07 | Phase 3 | Pending |
| ADMIN-08 | Phase 3 | Pending |
| ADMIN-09 | Phase 3 | Pending |
| ADMIN-10 | Phase 3 | Pending |
| TEACH-01 | Phase 4 | Pending |
| TEACH-02 | Phase 4 | Pending |
| TEACH-03 | Phase 4 | Pending |
| TEACH-04 | Phase 4 | Pending |
| CHKIN-01 | Phase 5 | Pending |
| CHKIN-02 | Phase 5 | Pending |
| CHKIN-03 | Phase 5 | Pending |
| CHKIN-04 | Phase 5 | Pending |
| CHKIN-05 | Phase 5 | Pending |
| CHKIN-06 | Phase 5 | Pending |
| CHKIN-07 | Phase 5 | Pending |
| MQTT-01 | Phase 6 | Pending |
| MQTT-02 | Phase 6 | Pending |
| MQTT-03 | Phase 6 | Pending |
| MQTT-04 | Phase 6 | Pending |
| MQTT-05 | Phase 6 | Pending |
| MQTT-06 | Phase 6 | Pending |
| MQTT-07 | Phase 6 | Pending |
| MQTT-08 | Phase 6 | Pending |
| MQTT-09 | Phase 6 | Pending |
| DUMMY-01 | Phase 7 | Pending |
| DUMMY-02 | Phase 7 | Pending |
| DUMMY-03 | Phase 7 | Pending |
| DUMMY-04 | Phase 7 | Pending |
| DUMMY-05 | Phase 7 | Pending |
| DUMMY-06 | Phase 7 | Pending |
| DUMMY-07 | Phase 7 | Pending |

**Coverage:**
- v1 requirements: 44 total
- Mapped to phases: 44
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-27*
*Last updated: 2026-03-27 after roadmap creation*
