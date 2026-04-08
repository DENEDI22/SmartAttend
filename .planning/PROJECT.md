# SmartAttend

## What This Is

SmartAttend is an NFC-based attendance tracking system for a Raspberry Pi server. ESP32 devices mounted in classrooms receive time-limited tokens via MQTT and write check-in URLs to NFC tags. Students tap their phone on the device, are taken to a web form, and log their attendance. Teachers and admins manage the system through a web UI served from the RPi.

## Core Value

Students can check in to a lesson by tapping their phone on the classroom NFC device — the entire flow from tap to attendance record must work reliably.

## Current State

**v1.1 Physical Devices shipped 2026-04-07.** Server exposed via ngrok, ESP32 firmware deployed and verified on hardware.

- Tech stack: FastAPI + Jinja2 + SQLAlchemy + SQLite + Mosquitto + paho-mqtt + APScheduler
- Docker Compose stack with 3 containers (server, mqtt, ngrok)
- ESP32 firmware at `ESP32THINGS/SmartAttend/SmartAttend.ino` (269 lines)
- 75 passing tests + 1 xfailed
- 9 phases shipped across 2 milestones (21 plans, 36 tasks)
- Timeline: 2026-03-27 → 2026-04-07 (12 days)

## Requirements

### Validated

- ✓ Project foundation: FastAPI app, SQLAlchemy models, Docker Compose stack boots on RPi — v1.0
- ✓ Auth: JWT-based login/logout with role-based access (admin, teacher, student) — v1.0
- ✓ Admin interface: device management, user management, schedule management — v1.0
- ✓ Teacher interface: attendance dashboard, attendance list per lesson, CSV export — v1.0
- ✓ Student check-in: NFC tap → browser → login → attendance record written — v1.0
- ✓ MQTT + Scheduler: token lifecycle end-to-end, dummy clients receive URLs — v1.0
- ✓ Dummy clients: 3 Python containers simulate ESP32 devices via MQTT — v1.0
- ✓ Mosquitto broker accessible on LAN for ESP32 WiFi connections — v1.1
- ✓ Ngrok container in Docker Compose, configured via `.env` — v1.1
- ✓ Check-in token URLs generated with ngrok public base URL — v1.1
- ✓ ESP32 firmware aligned to server MQTT contract (register, heartbeat, token subscribe) — v1.1
- ✓ ESP32 online-indicator LED on GPIO 13 — v1.1
- ✓ Dummy clients removed from Compose (one kept commented out for dev) — v1.1

### Active

- [ ] Student dashboard with attendance summary and detailed lesson list
- [ ] Password change (self-service for all users + admin reset for any user)
- [ ] "Verspätet" late threshold — global default with per-schedule-entry override
- [ ] Remove lux reading feature
- [ ] Extend check-in token validity from 60s to 90s
- [ ] Remove JWT 1h expiry for students (stay logged in until logout)
- [ ] CSV import for Users and Schedule entries (template + upload + validation preview)

## Current Milestone: v1.2 QOL Improvements

**Goal:** Quality-of-life improvements to attendance tracking — student visibility, late tracking, auth polish, and bulk data import.

**Target features:**
- Student dashboard with attendance summary stats and detailed lesson list (including late status)
- Password change (self-service for all users + admin reset)
- "Verspätet" late threshold — global default with per-schedule-entry override; shown on teacher and student dashboards
- Remove lux reading feature (MQTT handler, dummy client code)
- Extend check-in token validity from 60s to 90s
- Remove JWT 1h expiry for students — stay logged in until explicit logout
- CSV import for Users and Schedule entries with template download, upload, validation preview, and error highlighting

### Out of Scope

- Moodle API integration — attendance stored locally for now; Moodle write is future work
- RPi hardware power management (GPIO + RTC) — out of scope for this prototype
- Student NFC card check-in (Schülerausweis UID) — requires additional firmware work
- MQTT password-based auth — prototype uses anonymous; production hardening is future work
- OAuth / SSO login — username/password sufficient for school prototype
- Lux sensor readings — hardware sensor not connected yet

## Context

- **ESP32 firmware deployed.** Physical devices participate in the attendance flow — register, heartbeat, receive tokens, write NFC tags. Dummy clients removed from production compose.
- **Deployment target is a Raspberry Pi** — requires multi-arch Docker images (linux/arm64, linux/arm/v7). All dependencies must be available offline on the RPi.
- **Pico CSS** served from `static/` — no CDN, no JS framework, semantic HTML only. Works fully offline.
- **Docker Compose** runs 3 containers: server, MQTT broker, ngrok tunnel.
- **Ngrok** provides public HTTPS access to the RPi server for NFC check-in URLs.
- Device model has two independent flags: `is_enabled` (admin-controlled) and `is_online` (heartbeat-controlled). Scheduler only issues tokens when `is_enabled=True`.

## Constraints

- **Runtime**: Raspberry Pi (ARM) — Docker images must be multi-arch, all offline-capable
- **Tech Stack**: FastAPI + Jinja2 + SQLAlchemy + SQLite + Mosquitto + paho-mqtt + APScheduler + JWT (python-jose) + bcrypt (passlib) + Pico CSS
- **CSS**: Pico CSS, served locally from `static/` — no CDN, no JS builds
- **Database**: SQLite (sufficient for prototype, zero config)
- **ESP32**: Arduino framework, PubSubClient for MQTT, Adafruit PN532 for NFC

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python dummy clients instead of real ESP32 | No hardware available during dev; dummy client IS the firmware spec | ✓ Good — clean MQTT contract, easy to test |
| Docker Compose from Phase 1 | Always deployable to RPi; incremental functionality per phase | ✓ Good — stack always bootable |
| `is_enabled` flag separate from `is_online` | Admin must explicitly enable a device before tokens are issued | ✓ Good — clear separation of concerns |
| Pico CSS from static/ | Offline operation on RPi, no build step, semantic HTML | ✓ Good — zero JS build complexity |
| SQLite over PostgreSQL | Zero config, sufficient for school prototype scale | ✓ Good — single file DB, no container needed |
| JWT in HTTP-only cookie | Stateless auth; 8h for teachers/admins, 1h for students | ✓ Good — simple, secure |
| Half-open intervals for schedule overlap | `[start, end)` — avoids edge-case conflicts at boundaries | ✓ Good — clean conflict detection |
| Auto-register devices from MQTT heartbeat | Devices self-register on first message, admin enables later | ✓ Good — zero-touch device setup |
| Ngrok for public tunneling | Simple Docker container, configured via .env, no port forwarding needed | ✓ Good — works behind NAT on school network |
| BASE_URL with scheme+port | `http://localhost:8000` format for simple URL concatenation | ✓ Good — clean token URL generation |
| POC NFC functions verbatim in firmware | Proven code from POC, no refactor risk | ✓ Good — NFC writes worked first try |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition:**
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions

**After each milestone:**
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-08 after v1.2 milestone started*
