# SmartAttend

## What This Is

SmartAttend is an NFC-based attendance tracking system for a Raspberry Pi server. ESP32 devices mounted in classrooms receive time-limited tokens via MQTT and write check-in URLs to NFC tags. Students tap their phone on the device, are taken to a web form, and log their attendance. Teachers and admins manage the system through a web UI served from the RPi.

## Core Value

Students can check in to a lesson by tapping their phone on the classroom NFC device — the entire flow from tap to attendance record must work reliably.

## Current Milestone: v1.1 Physical Devices

**Goal:** Replace dummy clients with physical ESP32 devices and expose the system to the internet via ngrok.

**Target features:**
- Mosquitto broker accessible on LAN (ESP32 devices connect over WiFi)
- Ngrok container in Docker Compose, configured via `.env` (URL + auth token)
- Check-in token URLs generated with ngrok public base URL
- ESP32 firmware aligned to server MQTT contract (register, heartbeat, lux, token subscribe)
- ESP32 online-indicator LED on GPIO 13 (lit when MQTT connected)
- Dummy clients removed from Compose (one kept commented out for dev)

## Current State

**v1.0 MVP shipped 2026-03-31.** Full prototype operational with Python dummy clients simulating ESP32 devices.

- 3,506 lines of Python across 7 phases (18 plans)
- Tech stack: FastAPI + Jinja2 + SQLAlchemy + SQLite + Mosquitto + paho-mqtt + APScheduler
- Docker Compose stack with 6 containers (server, mqtt, 3 dummy clients, sqlite volume)
- 54 passing tests + 1 xfailed

## Requirements

### Validated

- [x] Project foundation: FastAPI app, SQLAlchemy models, Docker Compose stack boots on RPi — v1.0
- [x] Auth: JWT-based login/logout with role-based access (admin, teacher, student) — v1.0
- [x] Admin interface: device management, user management, schedule management — v1.0
- [x] Teacher interface: attendance dashboard, attendance list per lesson, CSV export — v1.0
- [x] Student check-in: NFC tap → browser → login → attendance record written — v1.0
- [x] MQTT + Scheduler: token lifecycle end-to-end, dummy clients receive URLs — v1.0
- [x] Dummy clients: 3 Python containers simulate ESP32 devices via MQTT — v1.0

### Active

- [ ] Mosquitto broker accessible on LAN for ESP32 WiFi connections
- [ ] Ngrok container in Docker Compose, configured via `.env` (URL + auth token)
- [ ] Check-in token URLs generated with ngrok public base URL
- [ ] ESP32 firmware aligned to server MQTT contract (register, heartbeat, lux, token subscribe)
- [ ] ESP32 online-indicator LED on GPIO 13 (lit when MQTT connected)
- [ ] Dummy clients removed from Compose (one kept commented out for dev)

### Out of Scope

- ESP32 firmware — prototype uses Python dummy clients; firmware is a future deliverable
- Moodle API integration — attendance stored locally for now; Moodle write is future work
- RPi hardware power management (GPIO + RTC) — out of scope for this prototype
- Student NFC card check-in (Schülerausweis UID) — requires ESP32 firmware
- MQTT password-based auth — prototype uses anonymous; production hardening is future work
- OAuth / SSO login — username/password sufficient for school prototype

## Context

- **No ESP32 hardware available during development.** Python dummy clients implement the identical MQTT contract (register, heartbeat, lux sensor, token subscribe) — the only difference is they print the URL instead of writing to NFC.
- **Deployment target is a Raspberry Pi** — requires multi-arch Docker images (linux/arm64, linux/arm/v7). All dependencies must be available offline on the RPi.
- **Pico CSS** served from `static/` — no CDN, no JS framework, semantic HTML only. Works fully offline.
- **Docker Compose** runs the full stack: server, MQTT broker, 3 dummy clients.
- Device model has two independent flags: `is_enabled` (admin-controlled) and `is_online` (heartbeat-controlled). Scheduler only issues tokens when `is_enabled=True`.

## Constraints

- **Hardware**: No ESP32 available — everything must work with Python dummy clients
- **Runtime**: Raspberry Pi (ARM) — Docker images must be multi-arch, all offline-capable
- **Tech Stack**: FastAPI + Jinja2 + SQLAlchemy + SQLite + Mosquitto + paho-mqtt + APScheduler + JWT (python-jose) + bcrypt (passlib) + Pico CSS
- **CSS**: Pico CSS, served locally from `static/` — no CDN, no JS builds
- **Database**: SQLite (sufficient for prototype, zero config)

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
*Last updated: 2026-04-02 after v1.1 milestone start*
