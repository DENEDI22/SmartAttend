---
phase: 4
slug: teacher-interface
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-29
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (already configured) |
| **Config file** | tests/conftest.py (exists) |
| **Quick run command** | `python -m pytest tests/test_teacher.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_teacher.py -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | TEACH-01 | integration | `pytest tests/test_teacher.py::test_dashboard_shows_todays_lessons -x` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | TEACH-01 | integration | `pytest tests/test_teacher.py::test_dashboard_empty_state -x` | ❌ W0 | ⬜ pending |
| 04-01-03 | 01 | 1 | TEACH-02 | integration | `pytest tests/test_teacher.py::test_dashboard_shows_attendance_count -x` | ❌ W0 | ⬜ pending |
| 04-01-04 | 01 | 1 | TEACH-02 | integration | `pytest tests/test_teacher.py::test_dashboard_no_token_shows_dash -x` | ❌ W0 | ⬜ pending |
| 04-01-05 | 01 | 1 | TEACH-03 | integration | `pytest tests/test_teacher.py::test_lesson_roster_full_class -x` | ❌ W0 | ⬜ pending |
| 04-01-06 | 01 | 1 | TEACH-03 | integration | `pytest tests/test_teacher.py::test_lesson_access_denied_other_teacher -x` | ❌ W0 | ⬜ pending |
| 04-01-07 | 01 | 1 | TEACH-04 | integration | `pytest tests/test_teacher.py::test_csv_export_content -x` | ❌ W0 | ⬜ pending |
| 04-01-08 | 01 | 1 | TEACH-04 | integration | `pytest tests/test_teacher.py::test_csv_encoding_and_format -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_teacher.py` — stubs for all TEACH requirements
- [ ] `teacher_client` fixture in `tests/conftest.py` — pre-authenticated teacher test client
- [ ] Seed fixtures for: ScheduleEntry + AttendanceToken + AttendanceRecord + multiple students

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CSV opens correctly in German Excel | TEACH-04 | Requires Excel + locale | Download CSV, open in Excel, verify Umlauts display correctly |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
