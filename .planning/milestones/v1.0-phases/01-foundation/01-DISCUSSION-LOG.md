# Phase 1: Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-27
**Phase:** 01-foundation
**Areas discussed:** Model fields, App package layout, DB init strategy

---

## Model Fields

### User model

| Option | Description | Selected |
|--------|-------------|----------|
| id, username, password_hash, role, class_name, is_active | Standard minimal set | |
| id, username, password_hash, role, is_active only | No class_name | |
| id, email, username, password_hash, role, class_name, is_active | With email | |
| Custom | User-specified | ✓ |

**User's choice:** `id, email, first_name, last_name, role, class_name, password_hash, is_active`
**Notes:** User specified all fields directly in free text. Uses email (not username) as login identifier.

---

### Device model

| Option | Description | Selected |
|--------|-------------|----------|
| id, device_id, room, label, is_enabled, is_online, last_seen, last_lux | Full set with label | ✓ |
| id, device_id, room, is_enabled, is_online, last_seen, last_lux | No label | |
| id, device_id, room, label, is_enabled, is_online, last_seen, last_lux, firmware_version | With firmware_version | |

**User's choice:** Standard recommended option — device_id, room, label, is_enabled, is_online, last_seen, last_lux.

---

### ScheduleEntry model

| Option | Description | Selected |
|--------|-------------|----------|
| id, device_id(FK), teacher_id(FK), class_name, subject, weekday, start_time, end_time | With subject | |
| Custom (no subject) | User dropped subject | ✓ |

**User's choice:** `id, device_id(FK), teacher_id(FK), class_name, weekday, start_time, end_time` — subject field dropped.
**Notes:** User explicitly removed `subject` from the model.

---

### AttendanceToken + AttendanceRecord

| Option | Description | Selected |
|--------|-------------|----------|
| Token without lesson_date / Record links to token | Minimal | |
| Token without lesson_date / Record links to schedule_entry directly | Denormalized | |
| Token with lesson_date / Record links to token | Per-day tracking | ✓ |

**User's choice:** Token includes `lesson_date`. Record links via `token_id`.
**Notes:** lesson_date distinguishes recurring weekly entries by calendar date.

---

## App Package Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Flat under app/ | app/models/, app/routers/, etc. | ✓ |
| Flat at project root | models/, routers/ at root | |

**User's choice:** `app/` subdirectory — standard FastAPI convention.

---

## DB Init Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| SQLAlchemy create_all() on startup | Simple, zero config | ✓ |
| Alembic from the start | Migration versioning | |
| create_all() now, Alembic later | Hybrid approach | |

**User's choice:** `create_all()` on startup — keep it simple for the prototype.

---

## Claude's Discretion

- Dummy client stub form in Phase 1
- Exact mosquitto.conf content
- .env.example variable list

## Deferred Ideas

None.
