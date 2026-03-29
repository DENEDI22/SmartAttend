# SmartAttend

## What This Is

SmartAttend is an NFC-based attendance tracking system for a Raspberry Pi server. ESP32 devices mounted in classrooms receive time-limited tokens via MQTT and write check-in URLs to NFC tags. Students tap their phone on the device, are taken to a web form, and log their attendance. Teachers and admins manage the system through a web UI served from the RPi.

## Core Value

Students can check in to a lesson by tapping their phone on the classroom NFC device — the entire flow from tap to attendance record must work reliably.

## Requirements

### Validated

- [x] Project foundation: FastAPI app, SQLAlchemy models, Docker Compose stack boots on RPi — Validated in Phase 1: Foundation
- [x] Auth: JWT-based login/logout with role-based access (admin, teacher, student) — Validated in Phase 2: Authentication
- [x] Admin interface: device management, user management, schedule management — Validated in Phase 3: Admin Interface

- [x] Teacher interface: attendance dashboard, attendance list per lesson, CSV export — Validated in Phase 4: Teacher Interface

### Active
- [ ] Student check-in: NFC tap → browser → login → attendance record written
- [ ] MQTT + Scheduler: token lifecycle end-to-end, dummy clients receive URLs
- [ ] Dummy clients: 3 Python processes simulate ESP32 devices via MQTT

### Out of Scope

- ESP32 firmware — prototype uses Python dummy clients; firmware is a future deliverable
- Moodle API integration — attendance stored locally for now; Moodle write is future work
- RPi hardware power management (GPIO + RTC) — out of scope for this prototype
- Student NFC card check-in (Schülerausweis UID) — future extension
- MQTT password-based auth — prototype uses anonymous; production hardening is future work

## Context

- **No ESP32 hardware available during development.** Python dummy clients implement the identical MQTT contract (register, heartbeat, lux sensor, token subscribe) — the only difference is they print the URL instead of writing to NFC.
- **Deployment target is a Raspberry Pi** — requires multi-arch Docker images (linux/arm64, linux/arm/v7). All dependencies must be available offline on the RPi.
- **Pico CSS** served from `static/` — no CDN, no JS framework, semantic HTML only. Works fully offline.
- **Docker Compose** is set up in Phase 1 so the stack is always deployable to the RPi, even during early development.
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
| Python dummy clients instead of real ESP32 | No hardware available during dev; dummy client IS the firmware spec | — Pending |
| Docker Compose from Phase 1 | Always deployable to RPi; incremental functionality per phase | — Pending |
| `is_enabled` flag separate from `is_online` | Admin must explicitly enable a device before tokens are issued | — Pending |
| Pico CSS from static/ | Offline operation on RPi, no build step, semantic HTML | — Pending |
| SQLite over PostgreSQL | Zero config, sufficient for school prototype scale | — Pending |
| JWT in HTTP-only cookie | Stateless auth; 8h for teachers/admins, 1h for students | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-29 — Phase 4 (Teacher Interface) complete*
