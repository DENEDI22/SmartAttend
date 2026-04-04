# SmartAttend

NFC-based attendance tracking system for schools. ESP32 devices in classrooms write time-limited check-in URLs to NFC tags. Students tap their phone, confirm attendance in a web form, and teachers see live results on their dashboard.

## How It Works

1. A scheduler on the server generates a unique check-in token for each active lesson and sends the URL to the classroom's ESP32 device via MQTT.
2. The ESP32 writes the URL as an NDEF record to its NFC tag.
3. A student taps their phone on the tag — the browser opens the check-in page.
4. The student confirms attendance (or logs in first if needed).
5. The server validates the token, matches the student to the lesson, and records attendance.
6. Teachers view attendance in real time and can export it as CSV.

Tokens rotate every minute and expire when the lesson ends. Duplicate check-ins are prevented automatically.

## Architecture

```
┌──────────┐  MQTT   ┌─────────────┐  HTTP   ┌──────────┐
│  ESP32   │◄────────│  Raspberry  │◄────────│  Student  │
│  + NFC   │────────►│  Pi Server  │────────►│  Phone    │
└──────────┘         └─────────────┘         └──────────┘
                      │  FastAPI    │
                      │  Mosquitto  │
                      │  SQLite     │
                      └─────────────┘
```

- **Server**: FastAPI + Jinja2, SQLAlchemy + SQLite, APScheduler, paho-mqtt
- **MQTT Broker**: Eclipse Mosquitto
- **Firmware**: Arduino (ESP32 + Adafruit PN532 NFC reader)
- **Styling**: Pico CSS (served locally, no JS build step)

## Setup

### Prerequisites

- Docker and Docker Compose
- An ESP32 with a PN532 NFC reader (optional — a dummy MQTT client is included for development)

### Server

```bash
cp .env.example .env   # fill in your values
docker compose up -d
```

The server is available at `http://localhost:8000`. An admin account is created on first boot using the credentials in `.env`.

For public access (so NFC URLs work outside the local network), enable the ngrok service in `docker-compose.yml` and set `NGROK_AUTHTOKEN`, `NGROK_DOMAIN`, and `BASE_URL` in `.env`.

A pre-built multi-arch image is available on Docker Hub:

```bash
docker pull denedi22/smartattend-server:latest
```

### ESP32 Firmware

1. Open `ESP32THINGS/SmartAttend/SmartAttend.ino` in the Arduino IDE.
2. Edit the WiFi and MQTT broker settings at the top of the file.
3. Flash to the ESP32.

The device connects to WiFi, registers itself with the server via MQTT, and waits for token URLs to write to NFC.

### Environment Variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | JWT signing key (generate with `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `DATABASE_URL` | SQLite path (default: `sqlite:////app/data/smartattend.db`) |
| `MQTT_BROKER` | Broker hostname (`mqtt` inside Docker Compose) |
| `MQTT_PORT` | Broker port (default: `1883`) |
| `BASE_URL` | Public URL used in NFC check-in links |
| `ADMIN_EMAIL` | Bootstrap admin email |
| `ADMIN_PASSWORD` | Bootstrap admin password |
| `NGROK_AUTHTOKEN` | Ngrok auth token (optional) |
| `NGROK_DOMAIN` | Reserved ngrok domain (optional) |

## User Roles

- **Admin** — manages devices, users, and lesson schedules at `/admin`.
- **Teacher** — views live attendance and exports CSV at `/teacher`.
- **Student** — checks in by tapping the NFC device and confirming on the web form.

## License

University project — not licensed for redistribution.
