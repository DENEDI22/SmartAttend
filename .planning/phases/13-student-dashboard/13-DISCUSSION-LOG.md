# Phase 13: Student Dashboard - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-08
**Phase:** 13-student-dashboard
**Areas discussed:** Summary statistics layout, Lesson list scope & filtering

---

## Summary Statistics Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Stat row | Single horizontal row of numbers, compact | |
| Card grid | Separate `<article>` cards in CSS grid, one per stat | ✓ |
| You decide | Claude picks simplest Pico CSS approach | |

**User's choice:** Card grid
**Notes:** None

### Follow-up: Hero card vs equal weight

| Option | Description | Selected |
|--------|-------------|----------|
| Hero percentage | Attendance percentage bigger/prominent | |
| Equal weight | All 5 cards same size | ✓ |

**User's choice:** Equal weight

### Follow-up: Late count display

| Option | Description | Selected |
|--------|-------------|----------|
| Own card | Late as its own dedicated stat card | ✓ |
| Sub-note | Folded into Anwesend card as parenthetical | |

**User's choice:** Own card

---

## Lesson List Scope & Filtering

### Time scope

| Option | Description | Selected |
|--------|-------------|----------|
| All-time | Every lesson since account creation | |
| Current week/month | Recent window with navigation | |
| Last year | 12 months of history | ✓ |

**User's choice:** Last year (12 months)

### List structure

| Option | Description | Selected |
|--------|-------------|----------|
| Flat table | One long table sorted by date, newest first | |
| Grouped by month | Separate heading + table per month | ✓ |
| You decide | Claude picks approach | |

**User's choice:** Grouped by month

---

## Claude's Discretion

- Status display & color coding (Anwesend/Verspaetet/Abwesend visual treatment) — not discussed, Claude to follow teacher dashboard pattern

## Deferred Ideas

None
