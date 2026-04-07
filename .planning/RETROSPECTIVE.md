# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-31
**Phases:** 7 | **Plans:** 18 | **Timeline:** 4 days

### What Was Built
- Full NFC attendance tracking system: FastAPI server, admin/teacher/student web UIs, MQTT broker, scheduler, 3 dummy ESP32 clients
- 44 requirements implemented across 7 phases — zero orphan requirements
- Docker Compose stack with 6 containers, multi-arch capable for RPi deployment
- 54 passing tests covering auth, admin, check-in, MQTT, and dummy client behavior

### What Worked
- Phase-per-capability decomposition: each phase delivered an independently verifiable feature
- Docker Compose from Phase 1 meant the stack was always deployable — no "integration phase" needed
- Dummy clients as the firmware spec: the MQTT topic contract was clean and testable without hardware
- Pico CSS + semantic HTML: zero JS build complexity, fully offline

### What Was Inefficient
- Some ROADMAP.md plan checkboxes fell behind actual execution (progress table lagged)
- A few SUMMARY.md one-liners were missing or malformed (02-01 had a bug reference, 02-03/05-02 were empty)

### Patterns Established
- Half-open intervals `[start, end)` for schedule overlap detection
- Device auto-registration from MQTT heartbeat, admin enables separately
- JWT in HTTP-only cookie with role-based expiry (8h admin/teacher, 1h student)
- Inline-editable tables with JS dynamic form submission for admin CRUD
- Semicolon-delimited CSV with UTF-8 BOM for German locale compatibility

### Key Lessons
1. Define the MQTT topic contract early — it becomes the interface between server and clients
2. SQLite is perfectly sufficient for school-scale prototypes; zero config saves time
3. Pico CSS semantic HTML approach eliminates entire categories of frontend complexity

### Cost Observations
- Model mix: primarily balanced profile (sonnet for executors)
- Notable: 128 commits across 4 days, ~18 plans averaging ~7 commits each

---

## Milestone: v1.1 — Physical Devices

**Shipped:** 2026-04-07
**Phases:** 2 | **Plans:** 3 | **Timeline:** 7 days (2026-03-31 → 2026-04-07)

### What Was Built
- BASE_URL config migration replacing SERVER_IP across all config, scheduler, and env files
- Production Docker Compose topology with ngrok tunnel (3 active services, dummy clients removed)
- ESP32 firmware with MQTT registration, 30s heartbeat, NFC tag writing from token URLs, GPIO 13 LED indicator

### What Worked
- v1.0 dummy client MQTT contract paid off: ESP32 firmware was a straightforward port, no server changes needed
- POC NFC functions reused verbatim — proven code eliminated NFC debugging
- Ngrok as Docker container: simple `.env` configuration, works behind NAT on school network
- Small milestone scope (2 phases, 3 plans): focused and shipped quickly

### What Was Inefficient
- ROADMAP.md plan checkboxes still lagged behind actual execution (08-02 shown as incomplete when it was done)
- Hardware constraint (no ESP32 during dev) meant firmware was write-and-deploy — no iterative testing

### Patterns Established
- BASE_URL with scheme+port for URL concatenation (replaces split IP/port config)
- Ngrok tunnel as Docker Compose service for public access
- ESP32 `#define` config block at top of firmware for easy per-device customization

### Key Lessons
1. Dummy clients as firmware spec (v1.0 lesson) was validated — ESP32 firmware aligned to the exact same MQTT contract
2. Ngrok simplifies RPi deployment: no router port forwarding, no DNS
3. Keep POC code functions verbatim when they work — refactoring for style introduces risk

### Cost Observations
- 3 plans, ~6.5 minutes total execution
- Smallest milestone so far — scope was right-sized for hardware integration

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Timeline | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | 4 days | 7 | Initial project — established all patterns |
| v1.1 | 7 days | 2 | Hardware integration — ESP32 + ngrok |

### Cumulative Quality

| Milestone | Tests | Key Metric |
|-----------|-------|------------|
| v1.0 | 54 | 44/44 requirements traced and complete |
| v1.1 | 75 | 8/8 requirements traced and complete |

### Top Lessons (Verified Across Milestones)

1. Docker Compose from day one eliminates integration surprises
2. Dummy clients as firmware spec keeps MQTT contract clean and testable — **confirmed in v1.1** when ESP32 firmware needed zero server changes
3. Keep POC code verbatim when it works — refactoring for style introduces risk on hardware
