# Phase 5: Student Check-in - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-29
**Phase:** 05-student-check-in
**Areas discussed:** Check-in page content, Auth flow & check-in UX, Error states & messages, Check-in page scope

---

## Check-in Page Content

| Option | Description | Selected |
|--------|-------------|----------|
| Class, Teacher, Room, Time | Full info display | |
| Minimal: Room + Time only | Just Raum and Zeitraum | ✓ |
| You decide | Let Claude pick | |

**User's choice:** Minimal: Room + Time only. Also: show confirmation after check-in, and if already checked in, show the check-in time.

---

## Auth Flow & Check-in UX

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-redirect to login | Uses existing ?next= wiring from Phase 2 | ✓ |
| Embed login form | Login form directly on check-in page | |
| You decide | Let Claude pick | |

**User's choice:** Auto-redirect to login if needed.

---

## Error States & Messages

| Option | Description | Selected |
|--------|-------------|----------|
| Specific messages per case | Distinct German message per error type | ✓ |
| You decide | Let Claude pick | |

**User's choice:** Specific messages. Expired: "Diese Stunde ist bereits beendet." Invalid: "Ungültiger oder fehlender Token." Duplicate: "Sie haben sich bereits eingecheckt." + time. Non-student: "Nur Schüler können sich einchecken." Inactive: "Dieser Token ist nicht mehr gültig."

---

## Check-in Page Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Standalone card, no nav | Like login.html, minimal friction | |
| With student nav | student_base.html with nav (SmartAttend + Abmelden) | ✓ |
| You decide | Let Claude pick | |

**User's choice:** With student nav.

---

## Claude's Discretion

- Router file organization
- Template structure and blocks
- Whether to update existing /student landing
- POST endpoint URL path
- Token validation order

## Deferred Ideas

None — discussion stayed within phase scope.
