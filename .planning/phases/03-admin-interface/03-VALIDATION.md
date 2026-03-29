---
phase: 3
slug: admin-interface
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-29
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 |
| **Config file** | none — uses default discovery |
| **Quick run command** | `pytest tests/test_admin.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_admin.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | ADMIN-01 | integration | `pytest tests/test_admin.py::test_devices_page_shows_devices -x` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | ADMIN-02 | integration | `pytest tests/test_admin.py::test_update_device_room_label -x` | ❌ W0 | ⬜ pending |
| 03-01-03 | 01 | 1 | ADMIN-03 | integration | `pytest tests/test_admin.py::test_toggle_device_enabled -x` | ❌ W0 | ⬜ pending |
| 03-01-04 | 01 | 1 | ADMIN-04 | integration | `pytest tests/test_admin.py::test_users_page_shows_users -x` | ❌ W0 | ⬜ pending |
| 03-01-05 | 01 | 1 | ADMIN-05 | integration | `pytest tests/test_admin.py::test_create_user -x` | ❌ W0 | ⬜ pending |
| 03-01-06 | 01 | 1 | ADMIN-06 | integration | `pytest tests/test_admin.py::test_deactivate_user -x` | ❌ W0 | ⬜ pending |
| 03-01-07 | 01 | 1 | ADMIN-07 | integration | `pytest tests/test_admin.py::test_device_schedule_entries_shown -x` | ❌ W0 | ⬜ pending |
| 03-01-08 | 01 | 1 | ADMIN-08 | integration | `pytest tests/test_admin.py::test_add_schedule_entry -x` | ❌ W0 | ⬜ pending |
| 03-01-09 | 01 | 1 | ADMIN-09 | integration | `pytest tests/test_admin.py::test_schedule_conflict_rejected -x` | ❌ W0 | ⬜ pending |
| 03-01-10 | 01 | 1 | ADMIN-10 | integration | `pytest tests/test_admin.py::test_delete_schedule_entry -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_admin.py` — stubs for all 10 ADMIN requirements
- [ ] `tests/conftest.py` — admin-authenticated client fixture, device/user/schedule seed fixtures

*Existing test infrastructure (conftest.py, test_auth.py) provides base patterns.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Inline edit JS change detection | D-05/D-09 | JS behavior in browser | Load /admin/devices, edit a field, verify save/revert buttons activate |
| Schedule conflict inline validation | D-17 | JS + API interaction | Fill schedule form with conflicting time, verify button stays disabled |
| `<details>` expandable rows | D-07 | Browser rendering | Click device row, verify schedule section expands |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
