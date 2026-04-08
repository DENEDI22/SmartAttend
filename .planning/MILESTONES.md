# Milestones

## v1.2 QOL Improvements (Shipped: 2026-04-08)

**Phases completed:** 5 phases, 8 plans

**Key accomplishments:**

- Removed lux-sensor dead code, tuned token rotation to 90s, extended student sessions to 30 days
- Self-service password change for all roles with reusable form partial; admin password reset with dialog UI and crypto password generator
- SystemSetting key-value model with global/per-entry late threshold; three-state attendance (Anwesend/Verspätet/Abwesend) with color-coded display
- Student attendance dashboard with 5 stat cards and month-grouped lesson history
- CSV bulk import for users and schedules with template download, validation preview, overlap detection, and atomic confirm

---

## v1.1 Physical Devices (Shipped: 2026-04-07)

**Phases completed:** 2 phases, 3 plans, 5 tasks

**Key accomplishments:**

- Replaced SERVER_IP with BASE_URL across config, scheduler, and env files for ngrok-ready token URL generation
- Production Docker Compose topology with ngrok tunnel to server:8000, dummy clients removed, one dev client commented out
- Production ESP32 firmware with MQTT registration, 30s heartbeat, NFC tag writing from token URLs, and GPIO 13 LED indicator

---

## v1.0 MVP (Shipped: 2026-03-31)

**Phases completed:** 7 phases, 18 plans, 31 tasks

**Key accomplishments:**

- pytest scaffold with conftest fixture isolation and app/ skeleton with pydantic-settings v2 config and SQLAlchemy 2.0 DeclarativeBase database module
- Five SQLAlchemy 2.0 models (User, Device, ScheduleEntry, AttendanceToken, AttendanceRecord) with FK constraints, plus FastAPI lifespan app and 10-package pinned requirements.txt
- Full Docker Compose stack with Dockerfile (multi-arch capable), Mosquitto 2.0 broker config, 3 dummy client stubs, and .env documentation — all 5 containers boot cleanly
- 1. [Rule 1 - Bug] Module-level engine causes lifespan failure in tests
- HS256 JWT creation (8h admin/teacher, 1h student) with bcrypt via passlib and FastAPI cookie-based auth dependencies using jose JWTError catch-all for robust redirect behavior
- One-liner:
- SchoolClass model, admin router skeleton with nav, admin.js inline-edit JS, and 10 ADMIN test stubs with shared fixtures
- Device management page with inline-editable room/label table, per-row enable/disable toggle, and bulk save via JS dynamic form submission
- User CRUD with inline-edit table, create form with SchoolClass auto-create, and soft-delete deactivation
- Schedule CRUD with per-device expandable sections, half-open interval overlap detection, and JSON conflict-check API for JS validation
- Teacher dashboard at /teacher showing today's lessons with Klasse/Raum/Zeit/Anwesend columns, attendance counts from token+record queries, empty state handling, and 9-test scaffold
- Lesson attendance roster with full class present/absent display and semicolon-delimited CSV export with UTF-8 BOM
- Test scaffold with 11 stubs for check-in flow plus student_base.html and checkin.html templates with 4-state conditional rendering
- Paho MQTT service with device registration, heartbeat/lux handlers, and QoS 1 token publishing via threaded background loop
- APScheduler with 1-minute token issuance for active lessons and 30-second heartbeat timeout monitoring, wired into FastAPI lifespan
- paho-mqtt v2 dummy client publishing registration, heartbeat (30s), lux (60s), subscribing to token URLs with graceful SIGTERM shutdown
- Verified Dockerfile installs paho-mqtt==2.1.0 from requirements.txt with PYTHONUNBUFFERED=1 and all three client containers defined in docker-compose.yml

---
