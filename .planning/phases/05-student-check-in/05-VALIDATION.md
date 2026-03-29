---
phase: 5
slug: student-check-in
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-29
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none (uses defaults) |
| **Quick run command** | `python -m pytest tests/test_checkin.py -x` |
| **Full suite command** | `python -m pytest tests/ -x` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_checkin.py -x`
- **After every plan wave:** Run `python -m pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | CHKIN-01 | integration | `pytest tests/test_checkin.py::test_checkin_page_shows_lesson_info -x` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | CHKIN-02 | integration | `pytest tests/test_checkin.py::test_checkin_unauthenticated_redirects_to_login -x` | ❌ W0 | ⬜ pending |
| 05-01-03 | 01 | 1 | CHKIN-03 | integration | `pytest tests/test_checkin.py::test_checkin_post_validates_token -x` | ❌ W0 | ⬜ pending |
| 05-01-04 | 01 | 1 | CHKIN-04 | integration | `pytest tests/test_checkin.py::test_checkin_duplicate_rejected -x` | ❌ W0 | ⬜ pending |
| 05-01-05 | 01 | 1 | CHKIN-05 | integration | `pytest tests/test_checkin.py::test_checkin_success_writes_record -x` | ❌ W0 | ⬜ pending |
| 05-01-06 | 01 | 1 | CHKIN-06 | integration | `pytest tests/test_checkin.py::test_checkin_expired_token_error -x` | ❌ W0 | ⬜ pending |
| 05-01-07 | 01 | 1 | CHKIN-07 | integration | `pytest tests/test_checkin.py::test_checkin_invalid_token_error -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_checkin.py` — stubs for all CHKIN requirements
- [ ] `student_client` fixture in `tests/conftest.py` — authenticated student test client

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| NFC tap → browser → check-in flow | End-to-end | Requires NFC hardware + mobile browser | Tap NFC device, verify URL opens, log in, confirm attendance |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
