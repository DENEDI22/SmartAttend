# Phase 11: Password Management - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-08
**Phase:** 11-password-management
**Areas discussed:** Password form UX, Admin reset flow

---

## Password Form UX

| Option | Description | Selected |
|--------|-------------|----------|
| Dedicated /settings page | New 'Einstellungen' page, nav link in all base templates | |
| Dedicated /password page | Standalone page just for password change | |
| You decide | Claude picks based on codebase patterns | |

**User's choice:** Self-service password change on each role's dashboard page (student/teacher dashboard)
**Notes:** User specified this as free text — prefers it integrated into existing pages rather than a new page.

### Follow-up: Self-service location

| Option | Description | Selected |
|--------|-------------|----------|
| Nav link 'Passwort' | Link in nav to /password page | |
| On their dashboard | Password change section on student/teacher dashboard | ✓ |
| You decide | Claude picks | |

**User's choice:** On their dashboard
**Notes:** None

---

## Admin Reset Flow

### Reset method

| Option | Description | Selected |
|--------|-------------|----------|
| Admin types password | Manual password entry in popup | |
| Auto-generate + show | One-click random password generation | |
| Both options | Field to type OR button to auto-generate | ✓ |

**User's choice:** Both options
**Notes:** None

### Popup style

| Option | Description | Selected |
|--------|-------------|----------|
| `<dialog>` element | Native HTML dialog overlay, minimal JS | ✓ |
| Inline expand | Form row expands below user, pure form submission | |

**User's choice:** `<dialog>` element
**Notes:** User preferred the clean overlay approach with native HTML dialog.

---

## Claude's Discretion

- Error message wording (German)
- Auto-generated password format and length
- Minimal JS for dialog and auto-generate
- Form styling within Pico CSS
- Whether admin can change their own password via self-service or only admin page

## Deferred Ideas

None
