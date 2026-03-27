# SmartAttend – Implementation Plan

This document captures all design decisions made during planning. It is a companion to `idea.md`, which remains the reference for the full system specification. Everything here either refines, extends, or organizes the work described there.

---

## Guiding Constraint

**No ESP32 hardware is available during development.** The server and MQTT infrastructure are built in full. ESP32 clients are simulated by Python dummy clients that implement the exact same MQTT contract the firmware will later use. The only behavioral difference is output: dummy clients print the received URL to the console instead of writing it to an NFC tag.

---

## Technology Stack

Confirmed as specified in `idea.md`:

| Layer | Technology |
|---|---|
| Web framework | FastAPI |
| Templating | Jinja2 |
| ORM | SQLAlchemy |
| Database | SQLite |
| MQTT broker | Mosquitto (in Docker Compose) |
| MQTT client | paho-mqtt |
| Scheduler | APScheduler |
| Auth | JWT (python-jose) |
| Password hashing | bcrypt (passlib) |
| CSS framework | **Pico CSS** — served from `static/`, no CDN dependency, no JS, semantic HTML |

Pico CSS is served locally so the system works fully offline on the RPi.

---

## Device Model: Two Independent Flags

The `Device` model from `idea.md` is extended with one additional field:

```python
class Device(Base):
    __tablename__ = "devices"

    id            = Column(Integer, primary_key=True)
    device_id     = Column(String, unique=True, nullable=False)   # MAC-based
    room          = Column(String, nullable=True)
    label         = Column(String, nullable=True)
    is_enabled    = Column(Boolean, default=False)   # ADDED: admin-controlled
    is_online     = Column(Boolean, default=False)   # heartbeat-controlled
    last_seen     = Column(DateTime, nullable=True)
    last_lux      = Column(Float, nullable=True)
    registered_at = Column(DateTime, default=datetime.utcnow)
```

`is_enabled` and `is_online` are independent:

| Flag | Controlled by | Meaning |
|---|---|---|
| `is_enabled` | Admin toggle in UI | Server issues tokens for this device |
| `is_online` | MQTT heartbeat | Device is currently connected |

The token scheduler only processes devices where `is_enabled = True`.

---

## Device Registration Flow

`idea.md` specifies that devices register automatically on first boot via MQTT. This is preserved. The admin enable step is added on top:

1. Dummy client / ESP32 sends `devices/register` → server **auto-creates** the device record with `is_enabled=False`
2. Admin sees the device appear in the panel with status **"pending"**
3. Admin assigns room, optionally sets a label, and clicks **Enable**
4. `is_enabled` → `True` → scheduler begins issuing tokens for this device
5. Device receives token URLs via MQTT, NFC tag becomes live

Devices that are registered but not yet enabled are visible in the admin panel but receive no tokens.

---

## Dummy Client Design

Each dummy client is a standalone Python process that fully implements the ESP32 MQTT contract:

| Behavior | Dummy client | ESP32 firmware (later) |
|---|---|---|
| Startup | Publish `devices/register` | Same |
| Every 30s | Publish `devices/{id}/status` heartbeat | Same |
| Every 60s | Publish `sensors/{id}/lux` (configurable value) | Same |
| On token received | `print(f"[NFC] Would write: {url}")` | `nfc.write_ndef_url(url)` |

The NFC output is the only line that changes when moving from dummy client to firmware. This makes the dummy client the de facto firmware specification.

Each dummy client is configured entirely via environment variables:

```env
DEVICE_ID=esp32-e101
ROOM=E101
MQTT_BROKER=mqtt
MQTT_PORT=1883
LUX_VALUE=320.0
```

---

## Docker Strategy

Docker Compose is set up in **Phase 1** so the full stack can be deployed to the RPi at any point during development. Each phase adds functionality but the infrastructure is always runnable.

### Services

```yaml
services:
  mqtt:          # eclipse-mosquitto:2
  server:        # FastAPI app (multi-arch image)
  client-e101:   # dummy client, room E101
  client-e102:   # dummy client, room E102
  client-e103:   # dummy client, room E103
```

### Multi-arch build (from dev machine)

```bash
docker buildx build \
  --platform linux/arm64,linux/arm/v7 \
  -t youruser/smartattend-server:latest \
  --push .
```

The RPi runs `docker compose pull && docker compose up -d` to update.

### Mosquitto config

```
listener 1883
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
```

For a real school deployment, replace `allow_anonymous true` with password-based auth.

---

## Phase Plan

### Phase 1 — Foundation + Docker

- Project folder structure (as defined in `idea.md`)
- `config.py` — pydantic-settings, reads `.env`
- `database.py` — SQLAlchemy engine, session factory, `Base`
- All 5 models: `User`, `Device` (with `is_enabled`), `ScheduleEntry`, `AttendanceToken`, `AttendanceRecord`
- `Dockerfile` for server (multi-arch)
- `docker-compose.yml` — server + mqtt + 3 dummy client stubs
- `mosquitto/config/mosquitto.conf`
- `.env.example`
- Dummy client stub: connects to MQTT, does nothing yet
- **Goal**: `docker compose up` boots cleanly on the Pi

### Phase 2 — Authentication

- `routers/auth.py` — POST `/auth/login`, POST `/auth/logout`, GET `/auth/me`
- JWT creation and validation (`python-jose`)
- Password hashing (`passlib/bcrypt`)
- `require_role(*roles)` dependency
- `templates/login.html`
- HTTP-only cookie session (8h teachers/admins, 1h students)
- **Goal**: login/logout works end-to-end, protected routes return 403 for wrong roles

### Phase 3 — Admin Interface

- `routers/admin.py` with all routes from `idea.md`
- Device management: list all devices, enable/disable toggle, assign room + label
- User management: list, create, deactivate (soft delete)
- Schedule management: list full timetable, add entry, remove entry (conflict check: same device + same time = rejected)
- Templates: `dashboard_admin.html`, `devices.html`, `admin_users.html`, `admin_schedule.html`
- **Goal**: admin can manage the entire system from the web UI

### Phase 4 — Teacher Interface

- `routers/teacher.py` with all routes from `idea.md`
- Dashboard: today's lessons with checked-in vs. expected count
- Attendance list per lesson
- CSV export per lesson
- Templates: `dashboard_teacher.html`, `attendance.html`
- **Goal**: teacher can monitor and export attendance for their lessons

### Phase 5 — Student Check-in

- `routers/student.py` — GET `/checkin`, POST `/checkin`
- Token lookup: exists? active? not expired?
- Duplicate check: student not already checked in for this lesson?
- Attendance record write on success
- Template: `checkin.html` — shows lesson info, login form (or uses existing cookie)
- Error states: expired token ("Diese Stunde ist bereits beendet"), duplicate check-in, invalid token
- **Goal**: full check-in flow works without hardware (token generated manually via DB for testing)

### Phase 6 — MQTT + Scheduler

- `services/mqtt_service.py` — paho-mqtt client, all handlers from `idea.md`
  - `on_message` dispatch: registration, heartbeat, sensor
  - `publish_token(device_id, url)`
  - `handle_registration` — upsert device, `is_enabled=False` on first create
  - `handle_heartbeat` — update `is_online`, `last_seen`
  - `handle_sensor` — update `last_lux`
- `services/token_service.py` — generate, deactivate, validate tokens
- `services/scheduler_service.py` — APScheduler, every-minute job, only processes `is_enabled=True` devices
- `services/sensor_service.py` — lux storage and logging
- **Goal**: full token lifecycle works end-to-end; dummy clients receive URLs via MQTT

### Phase 7 — Dummy Clients (complete)

- `dummy_client/` Python package
  - `main.py` — entry point, reads env vars, starts MQTT loop
  - `mqtt_handler.py` — all publish/subscribe logic
  - `nfc_stub.py` — `write_nfc_tag(url)` that prints to console
- `dummy_client/Dockerfile`
- Update `docker-compose.yml` — dummy clients fully wired, env vars per instance
- **Goal**: three dummy clients behave like real ESP32 devices; full system test possible on Pi without any hardware

---

## What Is Not Covered Here (Future)

These items are documented in `idea.md` under Future Extensions and are explicitly out of scope for this plan:

- ESP32 firmware
- Moodle API integration
- RPi hardware power management (GPIO + RTC)
- Student NFC card check-in (Schülerausweis UID)
- MQTT password-based auth for production
