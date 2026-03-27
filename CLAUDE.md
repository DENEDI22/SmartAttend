<!-- GSD:project-start source:PROJECT.md -->
## Project

**SmartAttend**

SmartAttend is an NFC-based attendance tracking system for a Raspberry Pi server. ESP32 devices mounted in classrooms receive time-limited tokens via MQTT and write check-in URLs to NFC tags. Students tap their phone on the device, are taken to a web form, and log their attendance. Teachers and admins manage the system through a web UI served from the RPi.

**Core Value:** Students can check in to a lesson by tapping their phone on the classroom NFC device — the entire flow from tap to attendance record must work reliably.

### Constraints

- **Hardware**: No ESP32 available — everything must work with Python dummy clients
- **Runtime**: Raspberry Pi (ARM) — Docker images must be multi-arch, all offline-capable
- **Tech Stack**: FastAPI + Jinja2 + SQLAlchemy + SQLite + Mosquitto + paho-mqtt + APScheduler + JWT (python-jose) + bcrypt (passlib) + Pico CSS
- **CSS**: Pico CSS, served locally from `static/` — no CDN, no JS builds
- **Database**: SQLite (sufficient for prototype, zero config)
<!-- GSD:project-end -->

<!-- GSD:stack-start source:STACK.md -->
## Technology Stack

Technology stack not yet documented. Will populate after codebase mapping or first phase.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
