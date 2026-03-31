# Phase 4: Teacher Interface - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-29
**Phase:** 04-teacher-interface
**Areas discussed:** Dashboard layout, Attendance list view, CSV export format, Nav & page structure

---

## Dashboard Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Card per lesson | Each lesson as Pico CSS article card | |
| Table view | Simple table with Klasse, Raum, Zeit, Anwesend columns | ✓ |
| You decide | Let Claude pick | |

**User's choice:** Table view.

### Follow-up: Expected student count

| Option | Description | Selected |
|--------|-------------|----------|
| Count students in class | COUNT active students with matching class_name | ✓ |
| You decide | Let Claude pick | |

**User's choice:** Count students in class.

---

## Attendance List View

| Option | Description | Selected |
|--------|-------------|----------|
| Full class roster with status | All students shown, checkmark for present, dash for absent | ✓ |
| Only checked-in students | Show only students who checked in | |
| You decide | Let Claude pick | |

**User's choice:** Full class roster with status.

---

## CSV Export Format

| Option | Description | Selected |
|--------|-------------|----------|
| Full roster with status | Nachname;Vorname;Klasse;Status;Uhrzeit with UTF-8 BOM, semicolon separator | ✓ |
| Only checked-in students | Export only checked-in students | |
| You decide | Let Claude pick | |

**User's choice:** Full roster with status. Semicolon separator for German Excel, UTF-8 BOM.

---

## Nav & Page Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Separate teacher_base.html | Own base template with teacher nav | ✓ |
| Reuse admin_base.html | Share admin base template | |
| You decide | Let Claude pick | |

**User's choice:** Separate teacher_base.html.

---

## Claude's Discretion

- Empty state for no lessons today
- Attendance list sorting order
- Handling missing AttendanceToken (lesson not yet started)
- Template file naming

## Deferred Ideas

None — discussion stayed within phase scope.
