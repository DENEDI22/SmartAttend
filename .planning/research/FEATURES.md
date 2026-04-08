# Feature Research

**Domain:** QOL improvements for NFC-based school attendance system
**Researched:** 2026-04-08
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features that complete the existing system. Without these, the product feels like a demo.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Student dashboard with attendance summary | Students currently see a blank placeholder page (`student.html` just says "tap device"). They have no visibility into their own attendance history. Every school system gives students read access to their records. | MEDIUM | Requires joining AttendanceRecord -> AttendanceToken -> ScheduleEntry to reconstruct lesson context (class, date, time, room). Must compute summary stats (total lessons, attended, missed, percentage). Display both summary cards and a detailed lesson list. |
| Password change (self-service) | Default passwords are set by admin. Users universally expect to change their own password. Current system has no `/password` or `/settings` route at all. | LOW | Simple form: current password + new password + confirm. Verify old password via `verify_password()`, hash new one via `get_password_hash()`. Add POST endpoint on auth router. Accessible to all roles. |
| Admin password reset for any user | Admin creates users with initial passwords but has no way to reset a forgotten password without DB access. Standard admin capability. | LOW | Add a "Reset Password" action to `/admin/users` page. Form takes new password, admin does not need to know old password. Reuses `get_password_hash()`. |
| Late threshold ("Verspaetet") | Teachers see "Anwesend/Abwesend" but not "late". In German schools, "Verspaetung" is tracked separately from absence. The `checked_in_at` timestamp already exists; the system just needs a threshold to classify it. | MEDIUM | Needs: (1) global default late threshold in minutes (config or DB setting), (2) optional per-ScheduleEntry override column `late_threshold_minutes`, (3) comparison logic: if `checked_in_at > start_time + threshold` then status="Verspaetet". Must update teacher lesson roster and student dashboard to show this third status. |
| Remove lux reading feature | `last_lux` field on Device, `sensors/+/lux` MQTT subscription, and `_handle_lux()` handler exist but hardware sensor is not connected (explicitly out of scope). Dead code confuses future developers. | LOW | Remove: `Device.last_lux` column, `_handle_lux()` in mqtt.py, `sensors/+/lux` subscription. Requires Alembic migration or manual DB column drop. Since SQLite is used and there is no Alembic setup, simplest approach is to leave column in DB but remove all code references, or add a migration step. |
| Extend token validity 60s -> 90s | Tokens rotate every 60s currently (scheduler interval). Students scanning NFC in the last seconds before rotation may get an expired token. 90s gives more breathing room. | LOW | The scheduler runs `_issue_tokens()` every 1 minute. Token expiry is set to `entry.end_time` (lesson end), not 60s. The "60s validity" refers to how often a new URL is written to the NFC tag. Change the scheduler interval from `IntervalTrigger(minutes=1)` to `IntervalTrigger(seconds=90)`. |
| Remove JWT 1h student expiry | Students log in once per school day. With 1h expiry, a student who logs in at 8:00 must re-login at 9:00 for their next check-in. Friction kills adoption. Teachers/admins already get 8h. | LOW | In `auth.py` login handler, change student expiry from `timedelta(hours=1)` to match admin/teacher (8h) or use a very long expiry (30 days) with cookie `max_age`. The requirement says "stay logged in until logout" which implies a long-lived token. Use 30 days with `max_age=30*86400`. |

### Differentiators (Competitive Advantage)

Features that elevate the system beyond basic attendance tracking.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| CSV import for Users | Admin currently creates users one-by-one via form. Schools have 200+ students. Bulk import from existing class lists (Excel/CSV) is the difference between "usable prototype" and "unusable in practice". | HIGH | Workflow: (1) download template CSV, (2) upload filled CSV, (3) server parses and validates (email format, required fields, duplicate detection, role validation, class_name auto-creation), (4) show preview table with row-by-row error highlighting, (5) admin confirms import. Must handle: encoding (UTF-8 BOM for German Excel), delimiter detection (comma vs semicolon), partial success (skip bad rows or reject all). |
| CSV import for Schedule entries | Same rationale as user import. A school with 20 classrooms and 40 lessons/week needs bulk schedule entry. Manual entry via form is impractical. | HIGH | Workflow mirrors user CSV import. Additional validations: device_id must exist, teacher email must resolve to existing teacher, weekday must be valid (0-6 or German name), time format parsing, overlap detection against existing entries. Preview must show conflicts. More complex than user import due to foreign key resolution. |
| Late status on student dashboard | Students see not just "present/absent" but also "late" with the exact time, helping them self-correct behavior. Teachers already have this via the roster. | LOW | Depends on late threshold feature. Once threshold logic exists, add a "Verspaetet" badge/status to the student's lesson list. Reuse the same comparison: `checked_in_at > start_time + threshold`. |
| Attendance percentage on student dashboard | Show "85% attendance rate" as a prominent number. Students and parents care about this metric. In German school systems attendance percentage can affect grades. | LOW | Simple calculation: `(attended_count / total_scheduled_count) * 100`. Must correctly count only past lessons (not future scheduled ones). Group by subject/class or show overall. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems for this project.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Real-time dashboard auto-refresh | Teachers want to see check-ins appear live | Requires WebSocket or SSR polling, adds JS complexity, breaks "no JS builds" constraint. Pico CSS is static. | Manual page refresh; teacher lesson page already shows current state on load. Add a simple meta-refresh tag (e.g., every 30s) if needed -- zero JS. |
| Email notifications for absences | Parents/teachers want alerts | Requires email server config (SMTP), RPi may not have internet, adds a whole notification subsystem. Out of scope for prototype. | Export CSV of absences; teacher reviews manually. |
| Student self-registration | Students create own accounts | Breaks admin control model. Admin must validate class assignment. Opens spam/abuse risk. | Admin creates accounts (single or CSV bulk import). |
| Granular per-student late thresholds | Some students have special arrangements | Adds UI complexity for edge case. Per-schedule-entry override already covers most needs (different thresholds for first period vs afternoon). | Use per-schedule-entry override. Teacher can note exceptions manually. |
| Multi-language support (i18n) | English version | All UI text is German (school in Germany). Adding i18n framework for a single-school prototype is over-engineering. | Keep German. All strings are in Jinja2 templates, easy to find if needed later. |
| Undo/audit log for CSV imports | "What if I import wrong data?" | Full audit logging is a separate feature with its own DB table, UI, and retention policy. | CSV import preview with confirmation step serves as the "undo" -- you review before committing. Admin can deactivate bad users after the fact. |

## Feature Dependencies

```
[Late threshold config]
    |
    +---> [Late status on teacher roster]
    |         (modify _build_roster() to add "Verspaetet" status)
    |
    +---> [Late status on student dashboard]
              (student dashboard shows late badge per lesson)

[Student dashboard]
    |
    +---> [Attendance percentage display]
    |         (summary stats at top of dashboard)
    |
    +---> [Late status on student dashboard]
              (requires both dashboard AND late threshold)

[Password change self-service]
    |
    +---> [Admin password reset]
              (shares get_password_hash; but no strict dependency --
               admin reset is simpler, can be built independently)

[Remove lux reading] ── independent, no dependencies

[Extend token validity] ── independent, no dependencies

[Remove JWT 1h student expiry] ── independent, no dependencies

[CSV user import]
    |
    +---> [CSV schedule import]
              (schedule import references users by email;
               importing users first ensures teachers exist)
```

### Dependency Notes

- **Late status on student dashboard requires both student dashboard AND late threshold:** The dashboard must exist before late badges can be added to it, and the threshold logic must exist to compute the status.
- **CSV schedule import benefits from CSV user import first:** Schedule entries reference teachers by ID. If teachers are not yet imported, schedule CSV validation will fail on teacher lookup. Build user import first.
- **Lux removal, token validity, and JWT changes are fully independent:** These are config/code cleanup tasks with no feature dependencies. They can be done in any order or in parallel.

## MVP Definition

### Launch With (v1.2 -- this milestone)

All features listed below are targeted for this milestone. Ordered by dependency and value.

- [x] Remove lux reading -- dead code cleanup, zero risk, do first
- [x] Extend token validity 60s -> 90s -- one-line config change
- [x] Remove JWT 1h student expiry -- one-line change in auth.py
- [x] Password change (self-service for all roles) -- high user value, low complexity
- [x] Admin password reset -- completes the password story
- [x] Late threshold with global default + per-entry override -- needed before dashboard shows late status
- [x] Student dashboard with summary + lesson list + late status -- highest user-facing value, depends on late threshold
- [x] CSV import for Users -- enables practical school deployment
- [x] CSV import for Schedule entries -- enables practical school deployment

### Add After Validation (v1.x)

- [ ] Historical attendance view for teachers (past dates, not just today) -- trigger: teachers ask "what about last Tuesday?"
- [ ] Admin dashboard with system-wide attendance statistics -- trigger: school leadership wants overview
- [ ] Attendance report generation (PDF) for parent meetings -- trigger: semester end

### Future Consideration (v2+)

- [ ] Moodle API integration -- explicitly out of scope per PROJECT.md
- [ ] Student NFC card check-in (UID-based) -- requires firmware work
- [ ] MQTT authentication -- production hardening
- [ ] OAuth/SSO -- enterprise feature, not needed for prototype

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority | Rationale |
|---------|------------|---------------------|----------|-----------|
| Student dashboard | HIGH | MEDIUM | P1 | Students have zero visibility today; this is the biggest UX gap |
| Late threshold | HIGH | MEDIUM | P1 | Teachers need to distinguish late from absent; required for dashboard |
| Password change (self-service) | HIGH | LOW | P1 | Universal expectation; blocks nothing; quick win |
| Admin password reset | MEDIUM | LOW | P1 | Completes admin user management story |
| CSV user import | HIGH | HIGH | P1 | Without bulk import, adding 200 students is impractical |
| CSV schedule import | HIGH | HIGH | P1 | Without bulk import, adding 40 schedule entries is impractical |
| Remove lux reading | LOW | LOW | P1 | Dead code removal; reduces confusion; trivial |
| Token validity 60s -> 90s | MEDIUM | LOW | P1 | One config change; reduces check-in failures |
| Remove JWT 1h student expiry | HIGH | LOW | P1 | Eliminates re-login friction for students |

**Priority key:**
- P1: Must have for this milestone (all v1.2 features are P1 by definition)
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Implementation Complexity Details

### Student Dashboard (MEDIUM)

**What to build:**
- New route `GET /student` replacing the current placeholder
- Query: join AttendanceRecord -> AttendanceToken -> ScheduleEntry to get lesson context
- Summary stats: total scheduled lessons (past only), attended count, missed count, late count, attendance percentage
- Lesson list table: date, class/subject, time, room, status (Anwesend/Verspaetet/Abwesend), check-in time
- Filter by date range or show last N weeks

**Existing infrastructure leveraged:**
- `student_base.html` template with nav already exists
- `require_role("student")` dependency works
- AttendanceRecord has `checked_in_at`, AttendanceToken has `lesson_date` and `schedule_entry_id`

**Key query:** For a student, find all ScheduleEntries where `class_name == student.class_name`, then for each past lesson date, check if an AttendanceRecord exists. This requires generating "expected lesson dates" from the weekly schedule, which is a moderately complex calendar computation.

**Simpler approach:** Only show lessons where a token was actually issued (AttendanceToken exists for that date). This avoids calendar generation and only counts days the system was running. More accurate for a prototype.

### Late Threshold (MEDIUM)

**Schema changes:**
- Add `late_threshold_minutes` (Integer, nullable, default NULL) to ScheduleEntry model
- Add a global setting -- either in Settings/config.py or a new `SystemSettings` table. Config.py is simpler: add `default_late_threshold_minutes: int = 5` to Settings.

**Logic:**
```python
def get_late_threshold(entry: ScheduleEntry) -> int:
    """Per-entry override wins, else global default."""
    if entry.late_threshold_minutes is not None:
        return entry.late_threshold_minutes
    return get_settings().default_late_threshold_minutes

def classify_attendance(checked_in_at, lesson_start, threshold_minutes):
    cutoff = lesson_start + timedelta(minutes=threshold_minutes)
    if checked_in_at <= cutoff:
        return "Anwesend"
    return "Verspaetet"
```

**UI changes:**
- Teacher roster: add "Verspaetet" as third status (yellow/orange styling)
- Teacher dashboard: show late count alongside checked-in count
- Admin schedule form: add optional late threshold field per entry
- Admin settings page (or just .env): global default

### CSV Import (HIGH)

**User CSV template columns:**
`Vorname;Nachname;E-Mail;Rolle;Klasse`

**Schedule CSV template columns:**
`Geraet-ID;Lehrer-E-Mail;Klasse;Wochentag;Startzeit;Endzeit`

**Validation rules (User CSV):**
- Required fields: Vorname, Nachname, E-Mail, Rolle
- Email format validation (regex or simple check)
- Email uniqueness (against existing DB + within CSV itself)
- Role must be admin/teacher/student
- Klasse required if role=student
- Generate default password (e.g., first initial + last name + "123") or require password column

**Validation rules (Schedule CSV):**
- Device ID must exist in DB
- Teacher email must resolve to existing user with role=teacher
- Weekday: accept 0-6 or German names (Montag-Sonntag)
- Time format: HH:MM
- start_time < end_time
- No overlap with existing schedule entries for same device+weekday
- Class name auto-created if not exists

**UX flow (both):**
1. `GET /admin/import/users` -- page with download template button + file upload form
2. `POST /admin/import/users/preview` -- parse CSV, validate all rows, return preview table
3. Preview table shows each row with green (valid) or red (error) highlighting + error message per row
4. Admin reviews, clicks "Import" button
5. `POST /admin/import/users/confirm` -- actually write to DB (only valid rows, or require all valid)
6. Show result: "X users imported, Y skipped"

**Technical approach:**
- Use Python `csv` module (already used for CSV export)
- Store parsed/validated data in session or hidden form fields between preview and confirm
- For "no JS" constraint: preview page is a full server-rendered page with the table
- Semicolon delimiter (German Excel default) with UTF-8 BOM support

## Competitor Feature Analysis

| Feature | Untis (Austrian/German standard) | Google Classroom | Our Approach |
|---------|----------------------------------|------------------|--------------|
| Student attendance view | Full history with filters, export | Basic present/absent per class | Summary stats + lesson list with late status; date-scoped |
| Password management | LDAP/AD integrated, no self-service | Google account (OAuth) | Self-service change + admin reset; simple bcrypt |
| Late tracking | Configurable per school, per period | Not tracked | Global default + per-schedule-entry override in minutes |
| Bulk import | CSV/XML with detailed mapping UI | Google Sheets integration | CSV with template download, preview, error highlighting |
| Check-in method | Manual teacher entry or card readers | Teacher marks attendance | NFC tap on ESP32 device (unique differentiator) |

## Sources

- Codebase analysis: existing models, routes, templates, and services in `/home/danylo/Documents/Vorlesungen/SmartAttend/app/`
- PROJECT.md requirements and constraints
- German school attendance conventions (Anwesend/Verspaetet/Abwesend is standard three-state model)
- Pico CSS constraints: no JS builds, semantic HTML only, offline-capable

---
*Feature research for: SmartAttend v1.2 QOL Improvements*
*Researched: 2026-04-08*
