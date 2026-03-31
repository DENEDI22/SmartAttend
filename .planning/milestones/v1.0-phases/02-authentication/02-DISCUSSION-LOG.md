# Phase 2: Authentication - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-27
**Areas discussed:** Login identifier, Auth failure UX, Post-login redirect, Admin bootstrap

---

## Login Identifier

**Q:** The User model has `email` as the unique field, no separate `username`. Should login use email as the identifier, or add a `username` field to the model?

| Option | Selected |
|--------|----------|
| Email as login handle | ✓ |
| Add `username` field | — |

**Notes:** No model change needed — `email` is already unique and indexed from Phase 1.

---

## Auth Failure UX

**Q1:** When login fails, how should the error be shown?

| Option | Selected |
|--------|----------|
| Inline flash on same page | ✓ |
| Redirect with query param | — |
| Stay on page, no reload (JS) | — |

**Q2:** What language for error messages?

| Option | Selected |
|--------|----------|
| German | ✓ |
| English | — |

**Q3:** When accessing a protected route without being logged in?

| Option | Selected |
|--------|----------|
| Redirect to /login | ✓ |
| Return 401 JSON | — |

---

## Post-Login Redirect

**Q1:** After successful login, where should the user land?

| Option | Selected |
|--------|----------|
| Role-based routing | ✓ |
| Always go to / | — |

**Q2:** Student role — where do they land?

| Option | Selected |
|--------|----------|
| Dedicated landing page | ✓ (with nuance) |
| Redirect to /checkin | — |

**User notes:** Students should land on a dedicated landing page if they logged in without a check-in token (visited /login manually). If they came via the NFC check-in flow, the `?next=` param should return them to the check-in URL. Implement redirect wiring in this phase; full check-in logic in Phase 5.

---

## Admin Bootstrap

**Q:** How is the first admin user created?

| Option | Selected |
|--------|----------|
| Env-var seed on startup | ✓ |
| Seed script / management command | — |
| Manual SQL / API call | — |

**Notes:** Idempotent — only creates admin if no admin exists. Runs in FastAPI lifespan.

---

*Discussion completed: 2026-03-27*
