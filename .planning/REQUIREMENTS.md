# Requirements: SmartAttend

**Defined:** 2026-04-08
**Core Value:** Students can check in to a lesson by tapping their phone on the classroom NFC device — the entire flow from tap to attendance record must work reliably.

## v1.2 Requirements

Requirements for QOL Improvements milestone. Each maps to roadmap phases.

### Cleanup

- [ ] **CLN-01**: Lux reading feature removed (MQTT handler, subscription, model references)
- [ ] **CLN-02**: Check-in token rotation interval extended from 60s to 90s
- [ ] **CLN-03**: Student JWT session extended to 30 days (stay logged in until logout)

### Password Management

- [ ] **PWD-01**: User can change their own password (current + new + confirm)
- [ ] **PWD-02**: Admin can reset any user's password without knowing the old one

### Late Tracking

- [ ] **LATE-01**: Global default late threshold configurable in minutes
- [ ] **LATE-02**: Per-schedule-entry late threshold override (NULL = use global default)
- [ ] **LATE-03**: Teacher lesson roster shows "Verspätet" as third status when student checked in after threshold
- [ ] **LATE-04**: Teacher dashboard shows late count alongside attendance count

### Student Dashboard

- [ ] **STUD-01**: Student can view attendance summary (total lessons, attended, missed, late, percentage)
- [ ] **STUD-02**: Student can view detailed lesson list with date, class, time, room, and status (Anwesend/Verspätet/Abwesend)

### CSV Import

- [ ] **CSV-01**: Admin can download a template CSV for user import
- [ ] **CSV-02**: Admin can upload a user CSV and see a validation preview with per-row error highlighting
- [ ] **CSV-03**: Admin can confirm user CSV import (only valid rows committed)
- [ ] **CSV-04**: Admin can download a template CSV for schedule import
- [ ] **CSV-05**: Admin can upload a schedule CSV and see a validation preview with overlap/FK errors
- [ ] **CSV-06**: Admin can confirm schedule CSV import (only valid rows committed)

## Future Requirements

Deferred to future release. Tracked but not in current roadmap.

### Reporting

- **RPT-01**: Teacher can view historical attendance for past dates (not just today)
- **RPT-02**: Admin can view system-wide attendance statistics dashboard
- **RPT-03**: Attendance report generation (PDF) for parent meetings

### Integration

- **INT-01**: Moodle API integration for attendance sync
- **INT-02**: Student NFC card check-in (UID-based, requires firmware work)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Real-time dashboard auto-refresh (WebSocket) | Breaks "no JS builds" constraint; manual refresh or meta-refresh sufficient |
| Email notifications for absences | Requires SMTP config, RPi may lack internet; CSV export covers reporting needs |
| Student self-registration | Breaks admin control model; CSV bulk import solves the scale problem |
| Per-student late thresholds | Per-schedule-entry override covers most cases; edge case complexity not justified |
| Multi-language (i18n) | Single German school; all strings in Jinja2 templates, easy to find later |
| Audit log for CSV imports | Preview-then-confirm serves as safeguard; admin can deactivate bad records after |
| Password version / session invalidation | Low threat model for school prototype; document limitation |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| — | — | — |

**Coverage:**
- v1.2 requirements: 15 total
- Mapped to phases: 0
- Unmapped: 15 ⚠️

---
*Requirements defined: 2026-04-08*
*Last updated: 2026-04-08 after initial definition*
