# SmartAttend – Server Documentation (Raspberry Pi)

## Overview

The Raspberry Pi acts as the central server for the entire SmartAttend system. It is responsible for:

- Generating and rotating time-limited attendance tokens on a schedule
- Publishing tokens to ESP32 clients via MQTT
- Serving the web application (student check-in, teacher dashboard, admin panel)
- Storing all attendance records, user accounts, and device configurations
- Receiving sensor data (light level) from clients and acting on it (power management)

All logic lives on the RPi. ESP32 clients are intentionally dumb — they receive a URL and write it to an NFC tag. Nothing more.

---

## Technology Stack

| Layer | Technology | Reason |
|---|---|---|
| Web framework | FastAPI | Async, fast, built-in OpenAPI docs |
| Templating | Jinja2 | Server-side rendered pages, no frontend build step |
| Database ORM | SQLAlchemy | Clean model definitions, easy migrations |
| Database | SQLite | Sufficient for prototype, zero config |
| MQTT broker | Mosquitto | Lightweight, runs natively on RPi |
| MQTT client (Python) | paho-mqtt | Standard library for MQTT in Python |
| Task scheduler | APScheduler | Cron-like jobs inside the Python process |
| Auth | JWT (python-jose) | Stateless token auth for API and web sessions |
| Password hashing | bcrypt (passlib) | Secure password storage |

---

## Project Structure

```
smartattend/
├── main.py                  # App entry point, mounts routers
├── config.py                # Settings (loaded from .env)
├── database.py              # SQLAlchemy engine + session factory
│
├── models/
│   ├── user.py              # User model
│   ├── device.py            # ESP32 device model
│   ├── schedule.py          # Timetable entry model
│   ├── token.py             # Active attendance token model
│   └── attendance.py        # Attendance record model
│
├── routers/
│   ├── auth.py              # Login, logout, session
│   ├── admin.py             # Device management, user management
│   ├── teacher.py           # View attendance, manage schedule
│   ├── student.py           # Check-in endpoint (NFC link lands here)
│   └── api.py               # Internal JSON API (device status, etc.)
│
├── services/
│   ├── token_service.py     # Token generation and validation logic
│   ├── mqtt_service.py      # MQTT client, publish/subscribe logic
│   ├── scheduler_service.py # APScheduler setup and job definitions
│   └── sensor_service.py    # Light sensor data processing
│
├── templates/
│   ├── base.html            # Base layout with nav
│   ├── login.html
│   ├── checkin.html         # Student-facing page (opened via NFC)
│   ├── dashboard_teacher.html
│   ├── dashboard_admin.html
│   └── devices.html         # Device management
│
└── static/
    ├── style.css
    └── app.js
```

---

## Database Models

### User

```python
class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True)
    username   = Column(String, unique=True, nullable=False)
    full_name  = Column(String, nullable=False)
    role       = Column(Enum("admin", "teacher", "student"), nullable=False)
    password   = Column(String, nullable=False)  # bcrypt hash
    class_name = Column(String, nullable=True)   # e.g. "FI22A" — students only
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active  = Column(Boolean, default=True)
```

Roles control what pages and API endpoints a user can access. Students only ever reach the check-in page. Teachers see their own lessons and attendance lists. Admins can manage everything.

---

### Device

```python
class Device(Base):
    __tablename__ = "devices"

    id           = Column(Integer, primary_key=True)
    device_id    = Column(String, unique=True, nullable=False)  # MAC-based, e.g. "esp32-a4b2c1"
    room         = Column(String, nullable=True)                # e.g. "E101"
    label        = Column(String, nullable=True)                # human-readable name
    last_seen    = Column(DateTime, nullable=True)
    is_online    = Column(Boolean, default=False)
    last_lux     = Column(Float, nullable=True)                 # latest light reading
    registered_at = Column(DateTime, default=datetime.utcnow)
```

Devices register themselves automatically on first boot via MQTT. The admin then assigns them to a room and optionally gives them a label. `device_id` is derived from the ESP32's MAC address to ensure it is stable across reboots.

---

### ScheduleEntry

```python
class ScheduleEntry(Base):
    __tablename__ = "schedule"

    id         = Column(Integer, primary_key=True)
    device_id  = Column(String, ForeignKey("devices.device_id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    class_name = Column(String, nullable=False)   # e.g. "FI22A"
    subject    = Column(String, nullable=False)   # e.g. "Netzwerktechnik"
    weekday    = Column(Integer, nullable=False)  # 0 = Monday, 6 = Sunday
    start_time = Column(Time, nullable=False)
    end_time   = Column(Time, nullable=False)
```

One device can have multiple schedule entries — one per lesson per day. The scheduler matches entries to the current time to decide when to generate a token and for which lesson.

---

### AttendanceToken

```python
class AttendanceToken(Base):
    __tablename__ = "attendance_tokens"

    id               = Column(Integer, primary_key=True)
    token            = Column(String, unique=True, nullable=False)  # UUID4
    schedule_entry_id = Column(Integer, ForeignKey("schedule.id"), nullable=False)
    device_id        = Column(String, nullable=False)
    created_at       = Column(DateTime, default=datetime.utcnow)
    expires_at       = Column(DateTime, nullable=False)
    is_active        = Column(Boolean, default=True)
```

Tokens are UUIDs. They are valid for the duration of the lesson (start_time → end_time). When a new token is generated for a device, the previous one is deactivated. The token itself is embedded in the URL that gets written to the NFC tag: `http://<rpi-ip>/checkin?token=<uuid>`.

---

### AttendanceRecord

```python
class AttendanceRecord(Base):
    __tablename__ = "attendance"

    id               = Column(Integer, primary_key=True)
    student_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    schedule_entry_id = Column(Integer, ForeignKey("schedule.id"), nullable=False)
    token_used       = Column(String, nullable=False)
    timestamp        = Column(DateTime, default=datetime.utcnow)
    device_id        = Column(String, nullable=False)
```

One record per student per lesson. Before writing, the server checks: (1) token exists and is active, (2) token has not expired, (3) student has not already checked in for this lesson. Duplicate check-ins are rejected.

---

## MQTT Topics

All communication between the RPi and ESP32 clients uses MQTT over the local WLAN. Mosquitto runs on the RPi and listens on port 1883.

| Topic | Direction | Payload | Purpose |
|---|---|---|---|
| `devices/register` | ESP32 → RPi | `{"device_id": "esp32-a4b2c1", "room": "E101"}` | Auto-registration on boot |
| `attendance/device/{device_id}` | RPi → ESP32 | `{"url": "http://192.168.1.10/checkin?token=..."}` | New token/URL to write to NFC |
| `devices/{device_id}/status` | ESP32 → RPi | `{"online": true}` | Heartbeat every 30s |
| `sensors/{device_id}/lux` | ESP32 → RPi | `{"lux": 342.5}` | Light sensor reading |

### MQTT Service (Python)

```python
# services/mqtt_service.py

client = mqtt.Client()
client.on_message = on_message
client.connect("localhost", 1883)
client.subscribe("devices/register")
client.subscribe("devices/+/status")
client.subscribe("sensors/+/lux")
client.loop_start()  # runs in background thread

def publish_token(device_id: str, url: str):
    topic = f"attendance/device/{device_id}"
    payload = json.dumps({"url": url})
    client.publish(topic, payload, qos=1)

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = json.loads(msg.payload)

    if topic == "devices/register":
        handle_registration(payload)
    elif "/status" in topic:
        handle_heartbeat(topic, payload)
    elif topic.startswith("sensors/"):
        handle_sensor(topic, payload)
```

---

## Token Generation & Scheduling

APScheduler runs inside the FastAPI process. Every minute it checks if any active schedule entry should have a token generated (or refreshed).

```python
# services/scheduler_service.py

scheduler = BackgroundScheduler()

@scheduler.scheduled_job("interval", minutes=1)
def check_and_issue_tokens():
    now = datetime.now()
    current_weekday = now.weekday()
    current_time = now.time()

    with get_db() as db:
        active_entries = db.query(ScheduleEntry).filter(
            ScheduleEntry.weekday == current_weekday,
            ScheduleEntry.start_time <= current_time,
            ScheduleEntry.end_time >= current_time
        ).all()

        for entry in active_entries:
            existing = db.query(AttendanceToken).filter(
                AttendanceToken.schedule_entry_id == entry.id,
                AttendanceToken.is_active == True
            ).first()

            if not existing:
                issue_new_token(entry, db)

def issue_new_token(entry: ScheduleEntry, db):
    # deactivate old token for this device
    db.query(AttendanceToken).filter(
        AttendanceToken.device_id == entry.device_id,
        AttendanceToken.is_active == True
    ).update({"is_active": False})

    token = str(uuid4())
    expires_at = datetime.combine(date.today(), entry.end_time)

    db.add(AttendanceToken(
        token=token,
        schedule_entry_id=entry.id,
        device_id=entry.device_id,
        expires_at=expires_at
    ))
    db.commit()

    url = f"http://{settings.SERVER_IP}/checkin?token={token}"
    mqtt_service.publish_token(entry.device_id, url)
```

---

## API Endpoints

### Authentication

| Method | Path | Description |
|---|---|---|
| POST | `/auth/login` | Username + password → sets session cookie |
| POST | `/auth/logout` | Clears session |
| GET | `/auth/me` | Returns current user info |

### Student Check-in

| Method | Path | Description |
|---|---|---|
| GET | `/checkin` | Renders check-in form. Reads `?token=` from URL. If token is invalid or expired, shows error. |
| POST | `/checkin` | Submits credentials + token. Validates everything and writes attendance record. |

The check-in flow for a student:
1. Tap phone on device → browser opens `/checkin?token=<uuid>`
2. Page shows lesson info (subject, teacher, room)
3. Student enters their username + password (or is already logged in via cookie)
4. Server validates: token active? not expired? student not already checked in?
5. Record written. Confirmation shown.

### Teacher Routes

| Method | Path | Description |
|---|---|---|
| GET | `/teacher/dashboard` | Overview of today's lessons |
| GET | `/teacher/attendance/{schedule_id}` | Attendance list for a specific lesson |
| GET | `/teacher/export/{schedule_id}` | Download attendance as CSV |

### Admin Routes

| Method | Path | Description |
|---|---|---|
| GET | `/admin/dashboard` | System overview: all devices, status |
| GET | `/admin/devices` | List all registered devices |
| POST | `/admin/devices/{device_id}/assign` | Assign device to a room |
| GET | `/admin/users` | List all users |
| POST | `/admin/users` | Create new user |
| DELETE | `/admin/users/{id}` | Deactivate user |
| GET | `/admin/schedule` | View full timetable |
| POST | `/admin/schedule` | Add schedule entry |
| DELETE | `/admin/schedule/{id}` | Remove schedule entry |

---

## Web Pages

### `/checkin` — Student Check-in

The only page students interact with. Opened automatically when they tap their phone on the device.

- Shows: lesson name, subject, teacher name, room
- If token is expired: clear error message ("Diese Stunde ist bereits beendet")
- If already checked in: confirmation without allowing duplicate
- After success: green confirmation screen, no further interaction needed
- No navigation to other pages — intentionally isolated

### `/teacher/dashboard` — Teacher Dashboard

- List of today's lessons for the logged-in teacher
- Each lesson shows: time, room, subject, class, how many students have checked in vs. expected
- Click on a lesson to open the full attendance list
- Export button (CSV) per lesson

### `/admin/dashboard` — Admin Overview

- All registered devices with online/offline status (updated via MQTT heartbeat)
- Last seen timestamp and last light reading per device
- Quick link to assign unassigned devices
- Summary stats: total students, total teachers, lessons today

### `/admin/devices` — Device Management

- Table of all ESP32 clients
- Columns: device_id, room assignment, label, status, last seen
- Form to assign device to a room and give it a label
- Unassigned devices highlighted

### `/admin/schedule` — Timetable

- Weekly grid view of all schedule entries across all devices
- Add entry: select device, teacher, class, subject, weekday, start/end time
- Entries for the same device on the same day at the same time are rejected

### `/admin/users` — User Management

- List of all users with role and class (for students)
- Create user form: name, username, password, role, class
- Deactivate user (soft delete — records are preserved)

---

## Sensor & Power Management

The BH1750 light sensor on each ESP32 client publishes lux readings every 60 seconds to `sensors/{device_id}/lux`. The server stores the latest reading per device.

Power management logic runs server-side:

```python
# services/sensor_service.py

LUX_THRESHOLD = 50  # below this = room considered empty

def handle_lux(device_id: str, lux: float, db):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if device:
        device.last_lux = lux
        db.commit()

    # If no active lesson is scheduled for this device right now,
    # and the room is dark, the server simply stops publishing tokens.
    # The ESP32 retains the last written URL in the NFC tag.
    # No action needed — the tag just becomes stale until the next token is issued.
```

For full RPi shutdown/wake behavior: this requires a hardware circuit (GPIO + RTC module or external trigger). For the prototype, the light sensor data is logged and displayed in the admin dashboard as an indicator of room occupancy. Full power cycling is documented as a future extension.

---

## Authentication & Security

- Passwords are hashed with bcrypt via `passlib`
- Sessions use signed JWT tokens stored in an HTTP-only cookie
- Token expiry: 8 hours for teachers/admins, 1 hour for students
- All `/teacher/*` and `/admin/*` routes are protected by role-based middleware
- The `/checkin` route is public (no login required before viewing the form) but requires valid credentials on submit
- Attendance tokens (UUIDs) are single-use per student — checked before writing the record

```python
# Dependency used on protected routes
def require_role(*roles):
    def dependency(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return current_user
    return dependency

# Usage in router
@router.get("/admin/users")
def list_users(user = Depends(require_role("admin")), db = Depends(get_db)):
    ...
```

---

## Configuration

All settings are loaded from a `.env` file via `pydantic-settings`:

```env
SERVER_IP=192.168.1.10
SECRET_KEY=change-this-in-production
DATABASE_URL=sqlite:///./smartattend.db
MQTT_BROKER=localhost
MQTT_PORT=1883
TOKEN_EXPIRE_MINUTES=480
LUX_THRESHOLD=50
```

---

## Deployment

The server is packaged as a Docker image and published to Docker Hub. The Raspberry Pi pulls and runs it via Docker Compose. Mosquitto runs as a separate container in the same Compose stack so everything is self-contained — no manual dependency installation on the RPi.

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 80

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
```

Build for ARM (Raspberry Pi is arm64/armv7) from a dev machine using buildx:

```bash
docker buildx build \
  --platform linux/arm64,linux/arm/v7 \
  -t yourdockerhubuser/smartattend-server:latest \
  --push .
```

### docker-compose.yml (runs on the RPi)

```yaml
services:
  server:
    image: yourdockerhubuser/smartattend-server:latest
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./data:/app/data        # SQLite database persists here
      - ./.env:/app/.env        # environment config
    environment:
      - DATABASE_URL=sqlite:///./data/smartattend.db
    depends_on:
      - mqtt
    network_mode: host          # needed so server can reach Mosquitto on localhost

  mqtt:
    image: eclipse-mosquitto:2
    restart: unless-stopped
    ports:
      - "1883:1883"
    volumes:
      - ./mosquitto/config:/mosquitto/config
      - ./mosquitto/data:/mosquitto/data
```

> **Note on `network_mode: host`**: ESP32 clients connect to the RPi's LAN IP directly. Using host networking simplifies this — both the FastAPI server and Mosquitto are reachable on the RPi's actual IP without extra port mapping gymnastics.

Minimal `mosquitto/config/mosquitto.conf`:

```
listener 1883
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
```

For a real school deployment, replace `allow_anonymous true` with password-based auth.

### Deploying on the RPi

```bash
# First time
git clone https://github.com/yourrepo/smartattend-deploy && cd smartattend-deploy
cp .env.example .env   # fill in SERVER_IP, SECRET_KEY, etc.
docker compose up -d

# Update to a new image version
docker compose pull
docker compose up -d
```

The SQLite database file lives in `./data/` on the RPi host, mounted into the container. It survives container restarts and image updates.

### Publishing a New Version

```bash
# From the dev machine
docker buildx build \
  --platform linux/arm64,linux/arm/v7 \
  -t yourdockerhubuser/smartattend-server:1.0.1 \
  -t yourdockerhubuser/smartattend-server:latest \
  --push .
```

Then on the RPi: `docker compose pull && docker compose up -d`.

---

## Future Extensions

- **Moodle API integration**: replace the local attendance DB writes with calls to Moodle's REST API (`mod_attendance_add_attendance`). The token and check-in flow stay identical — only the final write target changes.
- **RPi hardware power management**: use a RTC module (e.g. DS3231) + relay circuit to physically cut power to the RPi outside school hours. The light sensor data can feed into this decision.
- **Student NFC cards**: instead of a web form, students tap their personal NFC card (Schülerausweis) on the device — ESP32 reads the UID and sends it to the server. No phone required.