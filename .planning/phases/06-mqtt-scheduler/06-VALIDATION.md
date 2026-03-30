---
phase: 06
slug: mqtt-scheduler
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 06 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 |
| **Config file** | none — default discovery |
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
| 06-01-01 | 01 | 1 | MQTT-01 | unit (mock client) | `python -m pytest tests/test_mqtt.py::test_subscribe_topics -x` | No — W0 | pending |
| 06-01-02 | 01 | 1 | MQTT-02 | unit | `python -m pytest tests/test_mqtt.py::test_register_device -x` | No — W0 | pending |
| 06-01-03 | 01 | 1 | MQTT-03 | unit | `python -m pytest tests/test_mqtt.py::test_heartbeat_update -x` | No — W0 | pending |
| 06-01-04 | 01 | 1 | MQTT-04 | unit | `python -m pytest tests/test_mqtt.py::test_lux_update -x` | No — W0 | pending |
| 06-01-05 | 01 | 1 | MQTT-05 | unit (mock client) | `python -m pytest tests/test_mqtt.py::test_publish_token -x` | No — W0 | pending |
| 06-02-01 | 02 | 1 | MQTT-06 | unit | `python -m pytest tests/test_scheduler.py::test_issue_tokens -x` | No — W0 | pending |
| 06-02-02 | 02 | 1 | MQTT-07 | unit | `python -m pytest tests/test_scheduler.py::test_deactivate_previous_token -x` | No — W0 | pending |
| 06-02-03 | 02 | 1 | MQTT-08 | unit | `python -m pytest tests/test_scheduler.py::test_token_url_format -x` | No — W0 | pending |
| 06-02-04 | 02 | 1 | MQTT-09 | unit | `python -m pytest tests/test_scheduler.py::test_token_expiry -x` | No — W0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_mqtt.py` — stubs for MQTT-01 through MQTT-05 (mock paho client, test handler functions directly)
- [ ] `tests/test_scheduler.py` — stubs for MQTT-06 through MQTT-09 (mock MQTT publish, test scheduler job with real DB session)

*Existing `tests/conftest.py` already provides DB fixtures.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| MQTT reconnection after broker restart | N/A (Claude's discretion) | Requires Docker Compose restart | `docker compose restart mqtt` then check server logs for reconnection |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
