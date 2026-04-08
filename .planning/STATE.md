---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: QOL Improvements
status: Ready to plan
stopped_at: Completed 13-01-PLAN.md
last_updated: "2026-04-08T09:47:02.231Z"
progress:
  total_phases: 5
  completed_phases: 4
  total_plans: 6
  completed_plans: 6
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-08)

**Core value:** Students can check in to a lesson by tapping their phone on the classroom NFC device -- the entire flow from tap to attendance record must work reliably.
**Current focus:** Phase 13 — student-dashboard

## Current Position

Phase: 14
Plan: Not started

## Performance Metrics

**Velocity:**

- Total plans completed: 21 (v1.0 + v1.1)
- v1.0: 18 plans across 7 phases
- v1.1: 3 plans across 2 phases

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [v1.2 setup]: Zero new dependencies -- all features built on existing stack
- [v1.2 setup]: Late threshold uses NULL = global default pattern
- [v1.2 setup]: CSV import uses validate-then-commit with atomic transactions
- [Phase 10-cleanup]: Token rotation changed from 60s to 90s to reduce MQTT churn
- [Phase 10-cleanup]: Student JWT extended to 30 days for persistent login across browser restarts
- [Phase 11]: Validation order: length first, then match, then current password verify (fail fast)
- [Phase 11]: Admin password reset uses native HTML dialog with crypto.getRandomValues() for password generation
- [Phase 12-late-threshold]: SystemSetting uses key-value pattern with string values for flexibility
- [Phase 12-late-threshold]: Verspaetet students count toward checked_in total
- [Phase 13-student-dashboard]: Reuse exact late classification logic from teacher router for consistency

### Pending Todos

None.

### Blockers/Concerns

- JWT cookie max_age must change in lockstep with JWT expiry (CLN-03)
- CSV encoding: German Excel exports Windows-1252 -- needs encoding fallback
- Naive datetime consistency required for late threshold computation

## Session Continuity

Last session: 2026-04-08T09:45:49.432Z
Stopped at: Completed 13-01-PLAN.md
Resume file: None
