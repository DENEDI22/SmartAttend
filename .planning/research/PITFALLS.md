# Domain Pitfalls

**Domain:** QOL improvements to existing FastAPI + SQLite attendance system
**Researched:** 2026-04-08

## Critical Pitfalls

Mistakes that cause rewrites, data corruption, or security vulnerabilities.

### Pitfall 1: JWT Expiry Removal Invalidates All Existing Student Sessions

**What goes wrong:** Removing the 1h expiry for students means changing how `create_access_token` works. If the implementation changes the JWT payload structure (e.g., removing `exp` claim entirely or setting it to a far-future date), existing tokens with the old `exp` will still expire normally. Students who are currently logged in will be kicked out unexpectedly, or worse -- if `exp` is removed from the claim and `python-jose` is configured to require it, ALL existing tokens break immediately.

**Why it happens:** `python-jose`'s `jwt.decode()` validates `exp` by default. If you stop including `exp` in the token, old tokens still have it and work fine, but new tokens without `exp` will actually work too (jose skips validation if claim is absent). The real danger is the cookie `max_age` -- the current code sets `max_age=int(expires.total_seconds())` on the cookie itself. If you set a very long JWT expiry but forget to update `max_age`, the browser still deletes the cookie after 1 hour.

**Consequences:** Students still get logged out after 1 hour despite the "fix" because the cookie expires even though the JWT is still valid. Or if `max_age` is removed entirely, the cookie becomes a session cookie that vanishes when the browser closes -- worse than before.

**Prevention:**
- Change BOTH the JWT `expires_delta` AND the cookie `max_age` for students. They must stay in sync.
- Use a long-lived but not infinite expiry (e.g., 30 days) rather than removing `exp` entirely. Infinite sessions are a security risk if a student's account is compromised.
- Test with an actual browser (not just httpx in tests) to verify cookie persistence.

**Detection:** Students report being logged out despite the change. Check browser DevTools > Application > Cookies for `max_age` value.

### Pitfall 2: Password Change Without Session Invalidation

**What goes wrong:** After a user changes their password, their existing JWT remains valid until it expires. If a password was compromised and the user changes it, the attacker's stolen JWT still works.

**Why it happens:** JWTs are stateless -- the server has no way to invalidate an issued token. The current system has no token blacklist or version counter.

**Consequences:** Password change gives false sense of security. Compromised sessions remain active for up to 8 hours (teacher/admin) or until the new student expiry (potentially 30 days).

**Prevention:**
- Add a `password_version` integer column to the User model. Increment it on password change. Include it in the JWT payload. Check it in `get_current_user`. Mismatch = redirect to login.
- This is a lightweight alternative to a full token blacklist and works with the existing stateless architecture.
- Alternatively, since this is a school prototype, document the limitation and skip the complexity. Password compromise is low-risk in this context.

**Detection:** After changing password, open a second browser with the old session and verify it's rejected.

### Pitfall 3: CSV Import Creates Orphaned or Duplicate Records

**What goes wrong:** CSV import for users can create duplicates if email uniqueness isn't checked per-row before commit. CSV import for schedule entries can reference nonexistent teachers, devices, or classes. Partial failures in a batch leave the database in an inconsistent state.

**Why it happens:** CSV files from schools often have messy data: trailing whitespace, inconsistent capitalization, BOM characters, mixed encodings (Latin-1 vs UTF-8), semicolons vs commas as delimiter (German Excel defaults to semicolons).

**Consequences:** Duplicate users with slightly different emails (trailing space). Schedule entries pointing to wrong teachers. Half-imported batches with no way to roll back.

**Prevention:**
- Validate the ENTIRE CSV before writing anything. Show a preview with row-by-row validation status (green/red).
- Normalize all string fields: `strip()`, case-normalize emails to lowercase.
- Use a single database transaction for the entire import -- commit all or nothing.
- Detect delimiter automatically (sniff first line) or default to semicolon since this is a German school context.
- Handle BOM: `open(file, encoding='utf-8-sig')` strips UTF-8 BOM automatically.
- For schedule CSV: validate foreign keys exist (teacher email -> teacher_id, device_id exists, class exists or auto-create).

**Detection:** Check for duplicate emails after import. Verify row counts match expected.

### Pitfall 4: Late Threshold Comparison With Naive Datetimes

**What goes wrong:** The `checked_in_at` field on AttendanceRecord stores a naive `datetime` (no timezone info -- the model uses `DateTime` not `DateTime(timezone=True)`). The `start_time` on ScheduleEntry is a `time` object. Comparing these to determine "late" status requires combining `lesson_date` + `start_time` + `late_threshold` and comparing against `checked_in_at`. If `datetime.now()` is used inconsistently (some places naive, some aware), comparisons break silently.

**Why it happens:** The existing codebase uses `datetime.now()` (naive) everywhere except `create_access_token` which uses `datetime.now(timezone.utc)`. This inconsistency works fine currently because the server runs in a single timezone, but adding arithmetic (start_time + threshold minutes) makes it easy to accidentally mix aware and naive datetimes.

**Consequences:** Students marked as late when they were on time, or vice versa. Python raises `TypeError: can't compare offset-naive and offset-aware datetimes` if mixing occurs, crashing the page.

**Prevention:**
- Keep using naive datetimes consistently (the server and all users are in the same timezone on a school LAN). Do NOT introduce `timezone.utc` into the late calculation.
- The late check should be: `checked_in_at > datetime.combine(lesson_date, start_time) + timedelta(minutes=threshold)`.
- Add a test that creates a record exactly at threshold boundary and verifies the result.

**Detection:** TypeError exceptions in logs. Students incorrectly marked late on the dashboard.

## Moderate Pitfalls

### Pitfall 5: Student Dashboard N+1 Query Problem on SQLite

**What goes wrong:** The student dashboard needs to show all lessons the student's class had, with attendance status for each. The naive approach queries AttendanceRecord per lesson in a loop, generating O(n) queries where n = number of lessons in the semester.

**Why it happens:** Following the pattern in `teacher.py` where individual device/token lookups are done per lesson row. This works for teachers (who see only today's lessons, typically 1-5) but students see ALL historical lessons (potentially hundreds).

**Consequences:** Dashboard takes several seconds to load on a Raspberry Pi with SQLite. SQLite handles concurrent reads well but each query has overhead. With 100+ lessons and a Pi's limited I/O, this adds up.

**Prevention:**
- Use a single query with JOINs to fetch all attendance records for the student in one go. Build a lookup dict in Python.
- Query pattern: `SELECT schedule_entry_id, lesson_date, checked_in_at FROM attendance_records JOIN attendance_tokens ON ... WHERE student_id = :sid`
- Group results by (schedule_entry_id, lesson_date) in Python.
- Consider pagination (show current week/month by default, not all time).

### Pitfall 6: Password Change Form Without Current Password Verification

**What goes wrong:** Self-service password change accepts only new password without requiring the current password. If a student leaves their browser open and someone else accesses it, they can change the password.

**Why it happens:** Developers skip the "enter current password" step for simplicity. Admin password reset correctly skips this (admin is authenticated differently), but the same form gets reused for self-service.

**Prevention:**
- Self-service: require current password + new password + confirm new password.
- Admin reset: require only new password (admin is already authenticated as admin).
- Two separate endpoints: `POST /auth/change-password` (self-service) and `POST /admin/users/{id}/reset-password`.
- Validate new password minimum length (at least 8 characters for a school system).

### Pitfall 7: Late Threshold -- Global Default vs Per-Entry Override Confusion

**What goes wrong:** The data model for "late threshold" needs careful design. A global default (e.g., 5 minutes) should apply unless a specific ScheduleEntry overrides it. The naive approach adds a `late_threshold_minutes` column to ScheduleEntry and sets it for every entry. Then changing the global default requires updating every entry that should follow the default.

**Why it happens:** Conflating "use the default" with "explicitly set to 5 minutes" -- both store the same value, making it impossible to distinguish.

**Consequences:** Admin changes global default from 5 to 10 minutes. Entries that were explicitly set to 5 don't change (correct). Entries that should follow the default also don't change (incorrect) because they all stored "5" literally.

**Prevention:**
- Use `NULL` to mean "use global default." A non-NULL value means an explicit override.
- `late_threshold_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)`
- Store the global default in Settings/config (either `.env` or a new `settings` table).
- Resolution logic: `entry.late_threshold_minutes if entry.late_threshold_minutes is not None else global_default`
- Display "(Standard: 5 Min.)" vs "5 Min." in the UI to show which entries use default vs override.

### Pitfall 8: Lux Removal Breaks Existing Database Schema

**What goes wrong:** Removing the `last_lux` column from the Device model means existing SQLite databases have the column but the ORM doesn't expect it. SQLAlchemy won't crash (it ignores extra DB columns), but if you use Alembic migrations or `create_all()`, the column stays in the database forever as dead weight. If the removal isn't clean, the admin devices template still references `device.last_lux` and throws an `AttributeError`.

**Why it happens:** SQLite does not support `DROP COLUMN` in older versions (added in 3.35.0, 2021). The Raspberry Pi's system SQLite might be old enough to lack this.

**Consequences:** Template crash (`AttributeError: 'Device' object has no attribute 'last_lux'`) if the model column is removed but old DB has data. Or migration fails on old SQLite.

**Prevention:**
- Remove the column from the ORM model, the MQTT handler, and ALL templates referencing it.
- Do NOT try to drop the column from SQLite. Let it remain as a dead column in existing databases. SQLAlchemy will simply ignore it.
- If using `metadata.create_all()` for new databases, the column won't be created. Existing databases keep it harmlessly.
- Search for ALL references: model, mqtt handler, templates, tests.

### Pitfall 9: CSV Encoding Mismatch With German Characters

**What goes wrong:** German names contain umlauts (Mueller vs Muller, Schuler vs Schueler). Schools may export CSV from Excel which defaults to Windows-1252 encoding, not UTF-8. The upload handler assumes UTF-8 and corrupts names like "Muller" into "M\xfcller" garbled text.

**Why it happens:** Python's `csv.reader` defaults to UTF-8. German Excel (common in schools) exports as Windows-1252 by default unless the user explicitly chooses UTF-8.

**Prevention:**
- Try UTF-8 first (with BOM detection via `utf-8-sig`). If that fails with `UnicodeDecodeError`, fall back to `latin-1` (superset of Windows-1252 that never fails).
- Better: use `chardet` or a simple heuristic -- if the file starts with BOM, it's UTF-8. Otherwise try UTF-8, catch errors, fall back.
- Provide CSV templates for download that are already UTF-8 with BOM, so teachers filling in the template stay in UTF-8.

## Minor Pitfalls

### Pitfall 10: Token Validity Change (60s to 90s) Has No Code Change

**What goes wrong:** Developers search for "60" in the codebase expecting to find a hardcoded token validity. But the current scheduler doesn't use a fixed 60-second validity -- it creates tokens every 60 seconds (the scheduler interval) and sets `expires_at` to `datetime.combine(today, entry.end_time)`. The token is valid until the lesson ends, not for 60 seconds.

**Why it happens:** Misunderstanding the difference between "token rotation interval" (how often a new NFC URL is generated) and "token validity" (how long a token can be used for check-in). The `is_active` flag is what rotates -- old tokens are deactivated when new ones are created. But the check-in code checks `expires_at`, not `is_active` for the actual validation (it checks `is_active` first, then `expires_at`).

**Consequences:** Changing the scheduler interval from 60s to 90s actually means tokens rotate less frequently. The NFC device shows the same URL for 90s instead of 60s. This is the correct change, but the developer might also mistakenly change `expires_at` to `now + 90s` instead of keeping it at lesson end, which would break check-ins for students who tap later in the lesson.

**Prevention:**
- Only change the `IntervalTrigger(minutes=1)` to `IntervalTrigger(seconds=90)` in the scheduler.
- Do NOT change the `expires_at` calculation. Tokens should still expire at lesson end.
- Verify by reading the check-in flow: `_validate_token` checks `is_active` (rotated) and `expires_at` (lesson end). The inactive old tokens are still usable for check-in because `checkin.py` queries ALL tokens for the schedule_entry + lesson_date, not just the active one.

### Pitfall 11: Admin Password Reset Without Audit Trail

**What goes wrong:** Admin resets a student's password, but there's no record of when or by whom. In a school context, this can become a he-said-she-said situation.

**Prevention:** Log password resets with timestamp, admin user ID, and target user ID. A simple log line is sufficient for a prototype -- no need for a full audit table.

### Pitfall 12: Student Dashboard Shows Lessons From Wrong Class After Transfer

**What goes wrong:** If a student's `class_name` is changed (e.g., transferred from 10A to 10B), the dashboard query uses the current `class_name` to find schedule entries. Historical attendance records were made under the old class, so the dashboard either shows no records for those lessons (no schedule entry matching current class) or misattributes them.

**Prevention:** The attendance record is linked to a token, which links to a schedule_entry, which has its own `class_name`. For the student dashboard, follow the chain from AttendanceRecord -> AttendanceToken -> ScheduleEntry rather than filtering by `User.class_name`. This shows what the student actually attended, regardless of current class assignment.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Student dashboard | N+1 queries (Pitfall 5), wrong-class history (Pitfall 12) | Single JOIN query, follow record->token->entry chain |
| Password change | No session invalidation (Pitfall 2), missing current password check (Pitfall 6) | Add password_version to JWT, separate self-service vs admin endpoints |
| Late threshold | Naive datetime mixing (Pitfall 4), NULL-vs-explicit confusion (Pitfall 7) | Consistent naive datetimes, NULL = use default |
| CSV import | Encoding (Pitfall 9), duplicates/orphans (Pitfall 3) | Validate-then-commit, UTF-8-sig with Latin-1 fallback |
| Lux removal | Template references (Pitfall 8) | Grep for ALL lux references, don't drop SQLite column |
| Token validity | Misunderstanding rotation vs validity (Pitfall 10) | Only change scheduler interval, not expires_at |
| JWT expiry change | Cookie max_age mismatch (Pitfall 1) | Change JWT exp AND cookie max_age together |

## Sources

- Codebase analysis: `app/services/auth.py`, `app/routers/auth.py`, `app/dependencies.py` (JWT and cookie handling)
- Codebase analysis: `app/services/scheduler.py` (token issuance and rotation logic)
- Codebase analysis: `app/routers/teacher.py` (query patterns for dashboard)
- Codebase analysis: `app/routers/checkin.py` (token validation flow)
- Codebase analysis: `app/models/` (all model definitions, schema constraints)
- python-jose JWT behavior: training data, MEDIUM confidence (verify `exp` handling)
- SQLite DROP COLUMN support: added in SQLite 3.35.0, MEDIUM confidence
- Python csv module encoding: training data, HIGH confidence
