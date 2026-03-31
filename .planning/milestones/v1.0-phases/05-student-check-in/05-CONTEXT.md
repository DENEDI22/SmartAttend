# Phase 5: Student Check-in - Context

**Gathered:** 2026-03-29
**Status:** Ready for planning

<domain>
## Phase Boundary

A student can tap the NFC device, open the URL, and have their attendance recorded. The check-in page validates the token, shows lesson info, and writes an AttendanceRecord on confirmation. Handles expired, invalid, and duplicate check-in cases with German error messages.

</domain>

<decisions>
## Implementation Decisions

### Check-in Page Content
- **D-01:** Minimal display: Raum (from Device) and Zeitraum (start_time–end_time) only. No subject (ScheduleEntry has no subject field per Phase 1 D-07), no teacher name, no class.
- **D-02:** After successful check-in, show confirmation message on the same page.
- **D-03:** If the student has already checked in for this token, show the time of their check-in instead of the confirm button (e.g., "Eingecheckt um 08:02").

### Auth Flow
- **D-04:** GET `/checkin?token=X` requires authentication. If not authenticated, redirect to `/login?next=/checkin?token=X`. After login, student redirects back to check-in page. Uses existing `?next=` wiring from Phase 2 D-09.
- **D-05:** Only students can check in. Non-student roles see an error message.
- **D-06:** Check-in page has a single "Anwesenheit bestätigen" button. POST writes the AttendanceRecord and shows confirmation.

### Error States & Messages (German)
- **D-07:** Expired token: "Diese Stunde ist bereits beendet." (exact wording from CHKIN-06)
- **D-08:** Invalid or missing token: "Ungültiger oder fehlender Token."
- **D-09:** Duplicate check-in: "Sie haben sich bereits eingecheckt." + show check-in time: "Eingecheckt um HH:MM"
- **D-10:** Non-student role: "Nur Schüler können sich einchecken."
- **D-11:** Inactive token: "Dieser Token ist nicht mehr gültig."
- **D-12:** All errors displayed in the same centered card layout as the check-in page.

### Page Scope & Navigation
- **D-13:** Create `student_base.html` extending `base.html` with student nav: SmartAttend brand + Abmelden button. Same pattern as `admin_base.html` and `teacher_base.html`.
- **D-14:** Check-in template extends `student_base.html`. Centered `<article>` card (max-width 480px).
- **D-15:** Student router at `app/routers/student.py` with prefix — or add check-in routes to a new `app/routers/checkin.py`. Claude decides structure.

### Claude's Discretion
- Router file organization (checkin.py vs extending existing auth.py student route)
- Exact template structure and Jinja2 blocks
- Whether to update the existing `/student` landing page to use the new `student_base.html`
- POST endpoint URL path (`/checkin` vs `/checkin/confirm`)
- Token validation order (check existence → check active → check expiry → check duplicate)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements fully captured in decisions above and REQUIREMENTS.md (CHKIN-01 through CHKIN-07).

### Codebase References
- `app/models/attendance_token.py` — AttendanceToken model (token UUID, device_id, schedule_entry_id, lesson_date, is_active, expires_at)
- `app/models/attendance_record.py` — AttendanceRecord model (student_id, token_id, checked_in_at, unique constraint on student+token)
- `app/models/schedule_entry.py` — ScheduleEntry model (device_id, teacher_id, class_name, weekday, start_time, end_time)
- `app/models/device.py` — Device model (room, label)
- `app/routers/auth.py` — Login flow with `?next=` threading (lines 20-93), student landing at `/student`
- `app/templates/login.html` — Login form with hidden `next` field
- `app/templates/student.html` — Existing student landing page pattern
- `app/templates/admin_base.html` — Base template pattern to replicate for student_base.html
- `app/dependencies.py` — `get_current_user` and `require_role` dependencies

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/templates/login.html` — centered card pattern to replicate
- `app/templates/student.html` — student landing page (may be updated to use student_base.html)
- `app/dependencies.py` — `require_role("student")` for protecting check-in routes
- `app/routers/auth.py` — `?next=` redirect wiring already functional
- Phase 1 D-11: UniqueConstraint on (student_id, token_id) — DB-level duplicate prevention

### Established Patterns
- Centered `<article>` cards with max-width for single-action pages
- German-language UI text
- Pico CSS classless styling
- HTTP-only cookie auth with 303 redirects
- Error messages via template context variable (login.html pattern)

### Integration Points
- AttendanceToken.token (UUID string) — looked up from `?token=` query param
- AttendanceToken → ScheduleEntry → Device (join chain for room info)
- AttendanceRecord write with student_id from session + token_id from token lookup
- `datetime.now() > token.expires_at` for expiry check

</code_context>

<specifics>
## Specific Ideas

- Student sees minimal info (Room + Time only) — no clutter, just confirm and go
- Already-checked-in state shows the time instead of the button — no duplicate attempts
- Student nav with Abmelden — consistent with admin/teacher having their own base templates

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 05-student-check-in*
*Context gathered: 2026-03-29*
