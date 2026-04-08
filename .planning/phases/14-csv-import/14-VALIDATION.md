---
phase: 14
slug: csv-import
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-08
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | none — use pytest defaults |
| **Quick run command** | `python -m pytest tests/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 14-01-01 | 01 | 1 | CSV-01 | integration | `curl -o /dev/null -w '%{http_code}' /admin/csv/users/template` | ❌ W0 | ⬜ pending |
| 14-01-02 | 01 | 1 | CSV-02 | integration | `python -m pytest tests/test_csv_import.py -k user_upload` | ❌ W0 | ⬜ pending |
| 14-01-03 | 01 | 1 | CSV-03 | integration | `python -m pytest tests/test_csv_import.py -k user_confirm` | ❌ W0 | ⬜ pending |
| 14-02-01 | 02 | 1 | CSV-04 | integration | `curl -o /dev/null -w '%{http_code}' /admin/csv/schedule/template` | ❌ W0 | ⬜ pending |
| 14-02-02 | 02 | 1 | CSV-05 | integration | `python -m pytest tests/test_csv_import.py -k schedule_upload` | ❌ W0 | ⬜ pending |
| 14-02-03 | 02 | 1 | CSV-06 | integration | `python -m pytest tests/test_csv_import.py -k schedule_confirm` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_csv_import.py` — stubs for CSV-01 through CSV-06
- [ ] `tests/conftest.py` — shared fixtures (test client, DB session, test users)

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Red row highlighting in preview table | CSV-02, CSV-05 | Visual CSS styling | Upload CSV with errors, verify red rows in browser |
| File download triggers browser save dialog | CSV-01, CSV-04 | Browser behavior | Click template download, verify .csv file saves |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
