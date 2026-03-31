---
phase: 2
slug: authentication
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-27
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 |
| **Config file** | none — rootdir auto-detected as project root |
| **Quick run command** | `python3 -m pytest tests/test_auth.py -x -q` |
| **Full suite command** | `python3 -m pytest tests/ -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/test_auth.py -x -q`
- **After every plan wave:** Run `python3 -m pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 0 | AUTH-07 | integration | `python3 -m pytest tests/test_auth.py::test_login_page_renders -x` | Wave 0 | ⬜ pending |
| 02-01-02 | 01 | 0 | AUTH-07 | integration | `python3 -m pytest tests/test_auth.py::test_login_page_next_param -x` | Wave 0 | ⬜ pending |
| 02-01-03 | 01 | 1 | AUTH-01 | integration | `python3 -m pytest tests/test_auth.py::test_login_success -x` | Wave 0 | ⬜ pending |
| 02-01-04 | 01 | 1 | AUTH-01 | integration | `python3 -m pytest tests/test_auth.py::test_login_invalid_credentials -x` | Wave 0 | ⬜ pending |
| 02-01-05 | 01 | 1 | AUTH-01 | integration | `python3 -m pytest tests/test_auth.py::test_login_inactive_user -x` | Wave 0 | ⬜ pending |
| 02-02-01 | 02 | 1 | AUTH-02 | integration | `python3 -m pytest tests/test_auth.py::test_login_cookie_httponly -x` | Wave 0 | ⬜ pending |
| 02-02-02 | 02 | 1 | AUTH-03 | unit | `python3 -m pytest tests/test_auth.py::test_token_expiry_admin -x` | Wave 0 | ⬜ pending |
| 02-02-03 | 02 | 1 | AUTH-03 | unit | `python3 -m pytest tests/test_auth.py::test_token_expiry_student -x` | Wave 0 | ⬜ pending |
| 02-02-04 | 02 | 1 | AUTH-04 | integration | `python3 -m pytest tests/test_auth.py::test_logout -x` | Wave 0 | ⬜ pending |
| 02-02-05 | 02 | 1 | AUTH-05 | integration | `python3 -m pytest tests/test_auth.py::test_me_authenticated -x` | Wave 0 | ⬜ pending |
| 02-02-06 | 02 | 1 | AUTH-05 | integration | `python3 -m pytest tests/test_auth.py::test_me_unauthenticated -x` | Wave 0 | ⬜ pending |
| 02-03-01 | 03 | 1 | AUTH-06 | integration | `python3 -m pytest tests/test_auth.py::test_require_role_wrong_role -x` | Wave 0 | ⬜ pending |
| 02-03-02 | 03 | 1 | AUTH-06 | integration | `python3 -m pytest tests/test_auth.py::test_require_role_correct_role -x` | Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_auth.py` — stubs for AUTH-01 through AUTH-07 (all tests listed above)
- [ ] `tests/conftest.py` — extend `override_settings` fixture to include `ADMIN_EMAIL=""` and `ADMIN_PASSWORD=""` overrides; add `db_session` and `test_client` fixtures using `TestClient(app)`
- [ ] `app/static/pico.min.css` — download Pico CSS v2.1.1 once and commit; required before any template renders

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Admin seed creates account on first boot | D-13 | Requires fresh DB + env vars | Set `ADMIN_EMAIL=admin@test.com ADMIN_PASSWORD=secret` in `.env`, delete `data/smartattend.db`, run `docker compose up`, verify user row in DB |
| Student `?next=` redirect actually navigates back | D-09 | Full browser session needed | Start server, visit `/login?next=/checkin?token=fake`, log in as student, verify redirect to `/checkin?token=fake` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
