# Phase 11: Password Management - Context

**Gathered:** 2026-04-08
**Status:** Ready for planning

<domain>
## Phase Boundary

All users can change their own password. Admins can reset any user's password from the user management page. No email-based password reset (out of scope).

</domain>

<decisions>
## Implementation Decisions

### Self-service password change
- **D-01:** Password change form lives on each role's dashboard page (student dashboard, teacher dashboard) — not a separate page or nav link
- **D-02:** Form fields: current password, new password, confirm new password
- **D-03:** Reuse existing `verify_password()` and `get_password_hash()` from `app/services/auth.py`

### Admin password reset
- **D-04:** Reset button on `/admin/users` page next to each user row
- **D-05:** Opens a native HTML `<dialog>` element as overlay popup
- **D-06:** Dialog has both: a text field to type a new password AND a button to auto-generate a random password
- **D-07:** Auto-generated password is displayed in the dialog for admin to copy/share out-of-band

### Error handling
- **D-08:** Use existing redirect-with-query-params pattern (`?error=...`) for error messaging — consistent with current admin user CRUD

### Claude's Discretion
- Error message wording (German)
- Auto-generated password format and length
- Minimal JS for `<dialog>` showModal/close and auto-generate button
- Form styling within Pico CSS constraints
- Whether admin password change also goes through self-service form or only via admin page

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements fully captured in decisions above

### Codebase references
- `app/services/auth.py` — `verify_password()`, `get_password_hash()`, `authenticate_user()`
- `app/routers/admin.py` — Admin user management routes, existing create/deactivate patterns
- `app/routers/auth.py` — Login route, JWT creation, cookie handling
- `app/templates/admin_users.html` — User management table with inline-edit and actions
- `app/templates/student_base.html` — Student layout template with nav
- `app/templates/teacher_base.html` — Teacher layout template with nav

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `verify_password(plain, hashed)` in auth.py — validates current password
- `get_password_hash(password)` in auth.py — hashes new password with bcrypt
- `require_role()` dependency — already protects role-specific routes
- Admin users page already has per-row action buttons (deactivate)

### Established Patterns
- Error/success feedback via redirect query params (`?error=...`, `?msg=...`)
- Form submission via POST with `Form(...)` parameters
- Admin routes under `/admin/` prefix
- Templates extend role-specific base templates (`admin_base.html`, `student_base.html`, `teacher_base.html`)

### Integration Points
- New POST endpoint on auth router for self-service password change
- New POST endpoint on admin router for admin password reset
- `<dialog>` element added to `admin_users.html` template
- Password change form section added to student and teacher dashboard templates

</code_context>

<specifics>
## Specific Ideas

- Admin reset popup should feel lightweight — open dialog, type or generate password, confirm, done
- Self-service form on dashboard should be a clearly labeled section, not hidden

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 11-password-management*
*Context gathered: 2026-04-08*
