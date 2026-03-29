# Roadmap: SmartAttend

## Overview

SmartAttend is built in 7 phases that deliver the full NFC attendance flow. Phases begin with the project foundation and Docker stack, layer in authentication and admin/teacher interfaces, implement the student check-in flow, then wire up the MQTT broker and scheduler, and finish with the Python dummy clients that stand in for real ESP32 hardware. Each phase delivers a coherent, independently verifiable capability.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Project scaffold, all models, Docker Compose stack boots on RPi (completed 2026-03-27)
- [ ] **Phase 2: Authentication** - JWT login/logout with role-based access and HTTP-only cookies
- [ ] **Phase 3: Admin Interface** - Device management, user management, schedule management
- [ ] **Phase 4: Teacher Interface** - Attendance dashboard, lesson attendance list, CSV export
- [ ] **Phase 5: Student Check-in** - NFC tap to browser form to attendance record
- [ ] **Phase 6: MQTT & Scheduler** - Token lifecycle end-to-end, broker subscriptions, scheduler
- [ ] **Phase 7: Dummy Clients** - Three Python containers simulate ESP32 devices via MQTT

## Phase Details

### Phase 1: Foundation
**Goal**: The project compiles, runs, and is deployable to the Raspberry Pi from day one
**Depends on**: Nothing (first phase)
**Requirements**: FOUND-01, FOUND-02, FOUND-03, FOUND-04, FOUND-05, FOUND-06, FOUND-07, FOUND-08
**Success Criteria** (what must be TRUE):
  1. `docker compose up` starts server, MQTT broker, and stub containers without errors
  2. All 5 SQLAlchemy models (User, Device, ScheduleEntry, AttendanceToken, AttendanceRecord) exist and create their tables on first boot
  3. Configuration loads cleanly from `.env` via pydantic-settings with no hard-coded values
  4. The Docker image builds successfully for linux/arm64 and linux/arm/v7
  5. `.env.example` documents every required environment variable
**Plans**: 3 plans
Plans:
- [x] 01-01-PLAN.md — Test scaffold + project skeleton (config.py, database.py, directory layout)
- [x] 01-02-PLAN.md — All 5 SQLAlchemy models + main.py lifespan + requirements.txt
- [x] 01-03-PLAN.md — Docker layer (Dockerfile, mosquitto.conf, docker-compose.yml, .env.example)

### Phase 2: Authentication
**Goal**: Users can securely log in and out with roles enforced across all routes
**Depends on**: Phase 1
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, AUTH-06, AUTH-07
**Success Criteria** (what must be TRUE):
  1. User can log in at `/login` with username and password; a valid JWT is set as an HTTP-only cookie
  2. JWT expires after 8 hours for admin/teacher and 1 hour for students
  3. User can log out and the cookie is cleared
  4. Accessing a route with the wrong role returns a 403 response
  5. GET `/auth/me` returns the current user's info when authenticated
**Plans**: 3 plans
Plans:
- [x] 02-01-PLAN.md — Wave 0: test scaffold (13 stubs), conftest fixtures, Pico CSS download
- [x] 02-02-PLAN.md — Auth service layer (services/auth.py, dependencies.py, config additions)
- [x] 02-03-PLAN.md — Router, templates, main.py wiring, admin seed, all 13 tests green

### Phase 3: Admin Interface
**Goal**: Admin can manage devices, users, and the timetable through a web UI
**Depends on**: Phase 2
**Requirements**: ADMIN-01, ADMIN-02, ADMIN-03, ADMIN-04, ADMIN-05, ADMIN-06, ADMIN-07, ADMIN-08, ADMIN-09, ADMIN-10
**Success Criteria** (what must be TRUE):
  1. Admin can view all devices with their current status (online/offline, enabled/disabled, last seen, last lux) and assign a room label
  2. Admin can enable or disable a device, which controls whether the scheduler issues tokens for it
  3. Admin can create and deactivate users; deactivated users' attendance records are preserved
  4. Admin can add, view, and delete schedule entries; overlapping entries for the same device are rejected
**Plans**: 4 plans
Plans:
- [x] 03-01-PLAN.md — SchoolClass model, admin router skeleton, admin base template, test scaffold (10 stubs)
- [x] 03-02-PLAN.md — Device management page: table with inline editing, enable/disable toggle
- [x] 03-03-PLAN.md — User management page: table with create form, deactivate action
- [ ] 03-04-PLAN.md — Schedule CRUD: per-device expandable sections, conflict detection, all 10 tests green
**UI hint**: yes

### Phase 4: Teacher Interface
**Goal**: Teachers can monitor live attendance for their lessons and export records
**Depends on**: Phase 3
**Requirements**: TEACH-01, TEACH-02, TEACH-03, TEACH-04
**Success Criteria** (what must be TRUE):
  1. Teacher dashboard shows today's lessons with checked-in count vs expected student count
  2. Teacher can view the full attendance list for any specific lesson
  3. Teacher can download attendance for a lesson as a CSV file
**Plans**: TBD
**UI hint**: yes

### Phase 5: Student Check-in
**Goal**: A student can tap the NFC device, open the URL, and have their attendance recorded
**Depends on**: Phase 2
**Requirements**: CHKIN-01, CHKIN-02, CHKIN-03, CHKIN-04, CHKIN-05, CHKIN-06, CHKIN-07
**Success Criteria** (what must be TRUE):
  1. GET `/checkin?token=<uuid>` renders a page showing the lesson's subject, teacher, and room
  2. Student can log in on the check-in page and their attendance record is written on success
  3. Duplicate check-in by the same student for the same lesson is rejected
  4. An expired token shows a clear German-language error message ("Diese Stunde ist bereits beendet")
  5. An invalid or missing token shows an appropriate error instead of a server error
**Plans**: TBD
**UI hint**: yes

### Phase 6: MQTT & Scheduler
**Goal**: The server issues time-limited tokens to devices on a schedule and tracks device state via MQTT
**Depends on**: Phase 5
**Requirements**: MQTT-01, MQTT-02, MQTT-03, MQTT-04, MQTT-05, MQTT-06, MQTT-07, MQTT-08, MQTT-09
**Success Criteria** (what must be TRUE):
  1. A new device registration message auto-creates a device record in the database with `is_enabled=False`
  2. Heartbeat messages update `is_online` and `last_seen`; lux messages update `last_lux`
  3. The scheduler runs every minute and publishes a token URL to each active, enabled device with a current lesson; the URL follows the format `http://{SERVER_IP}/checkin?token={uuid}`
  4. When a new token is issued for a device, the previous token is deactivated
  5. Tokens expire at the lesson's `end_time`
**Plans**: TBD

### Phase 7: Dummy Clients
**Goal**: Three Python containers faithfully simulate ESP32 MQTT clients so the full flow can be tested without hardware
**Depends on**: Phase 6
**Requirements**: DUMMY-01, DUMMY-02, DUMMY-03, DUMMY-04, DUMMY-05, DUMMY-06, DUMMY-07
**Success Criteria** (what must be TRUE):
  1. Each dummy client publishes a registration message on startup and a heartbeat every 30 seconds
  2. Each dummy client publishes a lux sensor reading every 60 seconds with a configurable value
  3. When the server publishes a token URL, the dummy client prints it to its container log
  4. Three separate client containers (client-e101, client-e102, client-e103) start cleanly from `docker compose up`, each fully configured via environment variables
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 2/3 | Complete    | 2026-03-27 |
| 2. Authentication | 2/3 | In Progress|  |
| 3. Admin Interface | 1/4 | In Progress|  |
| 4. Teacher Interface | 0/? | Not started | - |
| 5. Student Check-in | 0/? | Not started | - |
| 6. MQTT & Scheduler | 0/? | Not started | - |
| 7. Dummy Clients | 0/? | Not started | - |
