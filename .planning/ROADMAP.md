# Roadmap: SmartAttend

## Milestones

- ✅ **v1.0 MVP** -- Phases 1-7 (shipped 2026-03-31)
- ✅ **v1.1 Physical Devices** -- Phases 8-9 (shipped 2026-04-07)
- 🚧 **v1.2 QOL Improvements** -- Phases 10-14 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-7) -- SHIPPED 2026-03-31</summary>

- [x] Phase 1: Foundation (3/3 plans) -- completed 2026-03-27
- [x] Phase 2: Authentication (3/3 plans) -- completed 2026-03-28
- [x] Phase 3: Admin Interface (4/4 plans) -- completed 2026-03-29
- [x] Phase 4: Teacher Interface (2/2 plans) -- completed 2026-03-30
- [x] Phase 5: Student Check-in (2/2 plans) -- completed 2026-03-30
- [x] Phase 6: MQTT & Scheduler (2/2 plans) -- completed 2026-03-30
- [x] Phase 7: Dummy Clients (2/2 plans) -- completed 2026-03-31

Full details: `.planning/milestones/v1.0-ROADMAP.md`

</details>

<details>
<summary>✅ v1.1 Physical Devices (Phases 8-9) -- SHIPPED 2026-04-07</summary>

- [x] Phase 8: Network & Public Access (2/2 plans) -- completed 2026-04-02
- [x] Phase 9: ESP32 Firmware (1/1 plan) -- completed 2026-04-02

Full details: `.planning/milestones/v1.1-ROADMAP.md`

</details>

### 🚧 v1.2 QOL Improvements (In Progress)

**Milestone Goal:** Quality-of-life improvements -- student visibility, late tracking, auth polish, and bulk data import.

- [x] **Phase 10: Cleanup** - Remove dead code and adjust token/session config for better UX (completed 2026-04-08)
- [x] **Phase 11: Password Management** - Self-service password change and admin password reset (completed 2026-04-08)
- [x] **Phase 12: Late Threshold** - Three-state attendance model with configurable late detection (completed 2026-04-08)
- [x] **Phase 13: Student Dashboard** - Attendance summary and detailed lesson history for students (completed 2026-04-08)
- [x] **Phase 14: CSV Import** - Bulk user and schedule creation via template-based CSV upload (completed 2026-04-08)

## Phase Details

### Phase 10: Cleanup
**Goal**: Dead code removed and token/session settings tuned so students stay logged in and check-in tokens last longer
**Depends on**: Phase 9 (v1.1 complete)
**Requirements**: CLN-01, CLN-02, CLN-03
**Success Criteria** (what must be TRUE):
  1. No lux-related code exists in MQTT handlers, models, dummy client, or templates
  2. Check-in tokens rotate every 90 seconds instead of 60 seconds
  3. Student can close browser, reopen days later, and still be logged in without re-entering credentials
**Plans**: 1 plan
Plans:
- [ ] 10-01-PLAN.md — Remove lux dead code and tune token/session lifetimes

### Phase 11: Password Management
**Goal**: All users can change their own password; admins can reset any user's password
**Depends on**: Phase 10
**Requirements**: PWD-01, PWD-02
**Success Criteria** (what must be TRUE):
  1. User can change their password by entering current password, new password, and confirmation
  2. User sees an error if current password is wrong or new passwords do not match
  3. Admin can reset any user's password from the user management page without knowing the old password
**Plans**: 2 plans
Plans:
- [x] 11-01-PLAN.md — Self-service password change (all roles)
- [x] 11-02-PLAN.md — Admin password reset with dialog UI
**UI hint**: yes

### Phase 12: Late Threshold
**Goal**: Attendance has three states (Anwesend / Verspaetet / Abwesend) with a configurable late threshold
**Depends on**: Phase 11
**Requirements**: LATE-01, LATE-02, LATE-03, LATE-04
**Success Criteria** (what must be TRUE):
  1. A global default late threshold (in minutes) is configurable and used when no per-entry override exists
  2. Admin or teacher can set a per-schedule-entry late threshold that overrides the global default
  3. Teacher lesson roster shows students who checked in after the threshold as "Verspaetet" (distinct from Anwesend and Abwesend)
  4. Teacher dashboard shows late count alongside present and absent counts for each lesson
**Plans**: 2 plans
Plans:
- [x] 12-01-PLAN.md — SystemSetting model, admin settings page, ScheduleEntry late column, schedule form field
- [ ] 12-02-PLAN.md — Three-state classification in roster/dashboard/CSV, colored template display
**UI hint**: yes

### Phase 13: Student Dashboard
**Goal**: Students can see their own attendance history with summary statistics and per-lesson detail
**Depends on**: Phase 12
**Requirements**: STUD-01, STUD-02
**Success Criteria** (what must be TRUE):
  1. Student sees a summary showing total lessons, attended, missed, late, and attendance percentage
  2. Student sees a detailed lesson list with date, class, time, room, and status (Anwesend / Verspaetet / Abwesend)
  3. Late status on the student dashboard matches the teacher's view for the same lesson
**Plans**: 1 plan
Plans:
- [x] 13-01-PLAN.md — Student dashboard with attendance summary stats and grouped lesson history
**UI hint**: yes

### Phase 14: CSV Import
**Goal**: Admins can bulk-create users and schedule entries by uploading CSV files with validation preview
**Depends on**: Phase 13
**Requirements**: CSV-01, CSV-02, CSV-03, CSV-04, CSV-05, CSV-06
**Success Criteria** (what must be TRUE):
  1. Admin can download a pre-formatted CSV template for user import and a separate template for schedule import
  2. Admin can upload a user CSV and see a validation preview where invalid rows are highlighted with specific error messages
  3. Admin can confirm user import and only valid rows are committed to the database
  4. Admin can upload a schedule CSV and see a validation preview showing overlap and foreign-key errors per row
  5. Admin can confirm schedule import and only valid rows are committed to the database
**Plans**: 2 plans
Plans:
- [x] 14-01-PLAN.md — User CSV import (template, upload/preview, confirm with upsert)
- [x] 14-02-PLAN.md — Schedule CSV import (template, upload/preview with overlap detection, confirm)
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 10 -> 11 -> 12 -> 13 -> 14

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 3/3 | Complete | 2026-03-27 |
| 2. Authentication | v1.0 | 3/3 | Complete | 2026-03-28 |
| 3. Admin Interface | v1.0 | 4/4 | Complete | 2026-03-29 |
| 4. Teacher Interface | v1.0 | 2/2 | Complete | 2026-03-30 |
| 5. Student Check-in | v1.0 | 2/2 | Complete | 2026-03-30 |
| 6. MQTT & Scheduler | v1.0 | 2/2 | Complete | 2026-03-30 |
| 7. Dummy Clients | v1.0 | 2/2 | Complete | 2026-03-31 |
| 8. Network & Public Access | v1.1 | 2/2 | Complete | 2026-04-02 |
| 9. ESP32 Firmware | v1.1 | 1/1 | Complete | 2026-04-02 |
| 10. Cleanup | v1.2 | 0/1 | Complete    | 2026-04-08 |
| 11. Password Management | v1.2 | 2/2 | Complete    | 2026-04-08 |
| 12. Late Threshold | v1.2 | 1/2 | Complete    | 2026-04-08 |
| 13. Student Dashboard | v1.2 | 1/1 | Complete    | 2026-04-08 |
| 14. CSV Import | v1.2 | 2/2 | Complete   | 2026-04-08 |
