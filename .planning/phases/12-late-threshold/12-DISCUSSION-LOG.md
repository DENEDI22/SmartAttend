# Phase 12: Late Threshold - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-08
**Phase:** 12-late-threshold
**Areas discussed:** Global default config, Teacher roster display, Schedule form UI

---

## Global Default Config

### Where to store

| Option | Description | Selected |
|--------|-------------|----------|
| .env only | DEFAULT_LATE_THRESHOLD_MINUTES in .env, requires restart | |
| Admin settings page | New /admin/settings page, runtime configurable | ✓ |
| .env + admin override | .env initial default, admin can change at runtime | |

**User's choice:** Admin settings page
**Notes:** User wants runtime configurability without restart.

### Default value

| Option | Description | Selected |
|--------|-------------|----------|
| 5 minutes | Strict | |
| 10 minutes | Moderate, common in German schools | ✓ |
| 15 minutes | Lenient | |

**User's choice:** 10 minutes

---

## Teacher Roster Display

### Visual style

| Option | Description | Selected |
|--------|-------------|----------|
| Text + color | Status text with green/orange/red colors | ✓ |
| Text only | Just text label, no colors | |
| You decide | Claude picks | |

**User's choice:** Text + color

### CSV export

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, as third status | CSV shows Anwesend/Verspätet/Abwesend | ✓ |
| Yes + check-in time | Status plus separate Uhrzeit column | |
| You decide | Claude picks | |

**User's choice:** Yes, as third status

---

## Schedule Form UI

### Per-entry override

| Option | Description | Selected |
|--------|-------------|----------|
| Optional number field | 'Verspätung (Min.)' field, empty = global default | ✓ |
| Dropdown with options | Pre-defined choices dropdown | |
| You decide | Claude picks | |

**User's choice:** Optional number field

---

## Claude's Discretion

- Admin settings page layout/styling
- SystemSetting table design
- Threshold cutoff edge case handling
- Whether to show threshold value on roster page

## Deferred Ideas

None
