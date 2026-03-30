---
phase: 07
slug: dummy-clients
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 07 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing suite) |
| **Config file** | tests/conftest.py (existing) |
| **Quick run command** | `python -m pytest tests/test_dummy_client.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_dummy_client.py -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 2 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | DUMMY-01 | unit (mock) | `python -m pytest tests/test_dummy_client.py::test_registration_on_connect -x` | No — W0 | pending |
| 07-01-02 | 01 | 1 | DUMMY-02 | unit (mock) | `python -m pytest tests/test_dummy_client.py::test_heartbeat_publishes -x` | No — W0 | pending |
| 07-01-03 | 01 | 1 | DUMMY-03 | unit (mock) | `python -m pytest tests/test_dummy_client.py::test_lux_publishes -x` | No — W0 | pending |
| 07-01-04 | 01 | 1 | DUMMY-04 | unit (mock) | `python -m pytest tests/test_dummy_client.py::test_token_url_logged -x` | No — W0 | pending |
| 07-01-05 | 01 | 1 | DUMMY-05 | unit | `python -m pytest tests/test_dummy_client.py::test_env_config -x` | No — W0 | pending |
| 07-01-06 | 01 | 1 | DUMMY-06 | manual | `docker compose build client-e101` | N/A | pending |
| 07-01-07 | 01 | 1 | DUMMY-07 | manual | `docker compose up -d client-e101 client-e102 client-e103` | N/A | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_dummy_client.py` — stubs for DUMMY-01 through DUMMY-05 (mock paho client, verify publish/subscribe calls)
- [ ] Import mechanism for `dummy_client/main.py` from test suite (sys.path or conftest fixture)

*Existing `tests/conftest.py` already provides DB fixtures.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dockerfile builds successfully | DUMMY-06 | Docker build needed | `docker compose build client-e101` |
| Three containers start cleanly | DUMMY-07 | Docker Compose needed | `docker compose up -d client-e101 client-e102 client-e103` then check `docker compose logs` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 2s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
