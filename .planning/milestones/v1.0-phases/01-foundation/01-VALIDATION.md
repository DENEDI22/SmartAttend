---
phase: 1
slug: foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-27
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (not yet installed — Wave 0 gap) |
| **Config file** | `pytest.ini` or `pyproject.toml [tool.pytest]` — Wave 0 installs |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_foundation.py -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | FOUND-01 | smoke | `pytest tests/test_foundation.py::test_directory_structure -x` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | FOUND-02 | unit | `pytest tests/test_foundation.py::test_config_loads -x` | ❌ W0 | ⬜ pending |
| 1-01-03 | 01 | 1 | FOUND-03 | unit | `pytest tests/test_foundation.py::test_database_session -x` | ❌ W0 | ⬜ pending |
| 1-01-04 | 01 | 1 | FOUND-04 | unit | `pytest tests/test_foundation.py::test_all_tables_created -x` | ❌ W0 | ⬜ pending |
| 1-01-05 | 01 | 2 | FOUND-05 | manual | manual — requires Docker daemon | manual-only | ⬜ pending |
| 1-01-06 | 01 | 2 | FOUND-06 | manual | manual — requires buildx | manual-only | ⬜ pending |
| 1-01-07 | 01 | 2 | FOUND-07 | manual | manual — requires Docker | manual-only | ⬜ pending |
| 1-01-08 | 01 | 1 | FOUND-08 | smoke | `pytest tests/test_foundation.py::test_env_example_complete -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/__init__.py` — makes tests a package
- [ ] `tests/conftest.py` — shared fixtures (tmp SQLite DB, test settings override)
- [ ] `tests/test_foundation.py` — stubs for FOUND-01, FOUND-02, FOUND-03, FOUND-04, FOUND-08
- [ ] Framework install: `pip install pytest pytest-anyio` (anyio needed for async FastAPI tests in later phases)

*Wave 0 must be created before any other task is executed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `docker compose up` starts all containers | FOUND-05 | Requires running Docker daemon | Run `docker compose up --build` and verify all containers reach healthy state |
| Multi-arch Docker image builds | FOUND-06 | Requires docker buildx + QEMU binfmt | Run `docker buildx build --platform linux/arm64,linux/arm/v7 .` and verify no errors |
| Mosquitto broker accepts connections | FOUND-07 | Requires running Docker container | Start compose stack and verify server container can connect to MQTT broker |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
