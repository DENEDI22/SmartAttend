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

## Cross-Milestone Trends

### Process Evolution

| Milestone | Timeline | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | 4 days | 7 | Initial project — established all patterns |

### Cumulative Quality

| Milestone | Tests | Key Metric |
|-----------|-------|------------|
| v1.0 | 54 | 44/44 requirements traced and complete |

### Top Lessons (Verified Across Milestones)

1. Docker Compose from day one eliminates integration surprises
2. Dummy clients as firmware spec keeps MQTT contract clean and testable
