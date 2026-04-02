# Roadmap: SmartAttend

## Milestones

- ✅ **v1.0 MVP** -- Phases 1-7 (shipped 2026-03-31)
- 🚧 **v1.1 Physical Devices** -- Phases 8-9 (in progress)

## Phases

<details>
<summary>v1.0 MVP (Phases 1-7) -- SHIPPED 2026-03-31</summary>

- [x] Phase 1: Foundation (3/3 plans) -- completed 2026-03-27
- [x] Phase 2: Authentication (3/3 plans) -- completed 2026-03-28
- [x] Phase 3: Admin Interface (4/4 plans) -- completed 2026-03-29
- [x] Phase 4: Teacher Interface (2/2 plans) -- completed 2026-03-30
- [x] Phase 5: Student Check-in (2/2 plans) -- completed 2026-03-30
- [x] Phase 6: MQTT & Scheduler (2/2 plans) -- completed 2026-03-30
- [x] Phase 7: Dummy Clients (2/2 plans) -- completed 2026-03-31

Full details: `.planning/milestones/v1.0-ROADMAP.md`

</details>

### v1.1 Physical Devices (In Progress)

**Milestone Goal:** Replace dummy clients with physical ESP32 devices and expose the system to the internet via ngrok.

- [ ] **Phase 8: Network & Public Access** - Mosquitto on LAN + ngrok tunnel + public token URLs + dummy client removal
- [ ] **Phase 9: ESP32 Firmware** - Firmware aligned to server MQTT contract with NFC write and LED indicator

## Phase Details

### Phase 8: Network & Public Access
**Goal**: The server is reachable from the internet, generates public check-in URLs, and Docker Compose reflects the production topology without dummy clients
**Depends on**: Phase 7 (v1.0 complete)
**Requirements**: NET-01, NET-02, NET-03, CLN-01
**Success Criteria** (what must be TRUE):
  1. An ESP32 on the same LAN can connect to the Mosquitto broker over WiFi (port 1883 exposed on host)
  2. Ngrok container starts with Docker Compose and establishes a tunnel to the server
  3. Check-in token URLs in MQTT messages use the ngrok public domain (not localhost)
  4. `docker compose up` starts only server, mqtt, and ngrok containers (no dummy clients running); one dummy client service remains commented out in docker-compose.yml for dev use
**Plans:** 2 plans
Plans:
- [x] 08-01-PLAN.md — BASE_URL config migration + test updates (NET-01, NET-03, NET-02 env vars)
- [ ] 08-02-PLAN.md — Docker Compose ngrok service + dummy client cleanup (NET-02, CLN-01)

### Phase 9: ESP32 Firmware
**Goal**: Physical ESP32 devices participate in the attendance flow -- registering, heartbeating, receiving tokens, and writing NFC tags
**Depends on**: Phase 8
**Requirements**: FW-01, FW-02, FW-03, FW-04
**Success Criteria** (what must be TRUE):
  1. ESP32 appears as a registered device in the admin UI after first boot (auto-registration via `devices/register`)
  2. ESP32 shows as "online" in the admin UI while running (heartbeat every 30s to `devices/{id}/status`)
  3. When a lesson is active, the ESP32 receives the token URL and writes it as an NDEF URI record to an NFC tag
  4. LED on GPIO 13 is lit when MQTT is connected and off when disconnected
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 8 -> 9

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 3/3 | Complete | 2026-03-27 |
| 2. Authentication | v1.0 | 3/3 | Complete | 2026-03-28 |
| 3. Admin Interface | v1.0 | 4/4 | Complete | 2026-03-29 |
| 4. Teacher Interface | v1.0 | 2/2 | Complete | 2026-03-30 |
| 5. Student Check-in | v1.0 | 2/2 | Complete | 2026-03-30 |
| 6. MQTT & Scheduler | v1.0 | 2/2 | Complete | 2026-03-30 |
| 7. Dummy Clients | v1.0 | 2/2 | Complete | 2026-03-31 |
| 8. Network & Public Access | v1.1 | 0/2 | Planning | - |
| 9. ESP32 Firmware | v1.1 | 0/0 | Not started | - |
