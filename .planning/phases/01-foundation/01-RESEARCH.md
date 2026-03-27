# Phase 1: Foundation - Research

**Researched:** 2026-03-27
**Domain:** FastAPI + SQLAlchemy 2.0 + pydantic-settings + Docker multi-arch + Mosquitto MQTT
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** All application code lives under `app/` subdirectory. Structure:
  ```
  SmartAttend/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py
  │   ├── config.py
  │   ├── database.py
  │   ├── models/
  │   ├── routers/
  │   ├── services/
  │   ├── templates/
  │   └── static/
  ├── dummy_client/
  ├── mosquitto/
  ├── docker-compose.yml
  └── Dockerfile
  ```
- **D-02:** Imports use `app.models.user`, `app.routers.auth`, etc.
- **D-03:** Use `SQLAlchemy Base.metadata.create_all()` called in FastAPI lifespan on startup. No Alembic. Tables are created automatically on first boot inside Docker.
- **D-04 (User model):** `id` (int PK), `email` (str, unique), `first_name` (str), `last_name` (str), `role` (str enum: admin/teacher/student), `class_name` (str, nullable), `password_hash` (str), `is_active` (bool, default True)
- **D-05 (Device model):** `id` (int PK), `device_id` (str, unique), `room` (str, nullable), `label` (str, nullable), `is_enabled` (bool, default False), `is_online` (bool, default False), `last_seen` (datetime, nullable), `last_lux` (float, nullable)
- **D-06 (ScheduleEntry model):** `id` (int PK), `device_id` (int FK → Device), `teacher_id` (int FK → User), `class_name` (str), `weekday` (int, 0=Monday–6=Sunday), `start_time` (time), `end_time` (time)
- **D-07:** No `subject` field on ScheduleEntry — dropped by user decision.
- **D-08 (AttendanceToken model):** `id` (int PK), `token` (str UUID, unique, indexed), `device_id` (int FK → Device), `schedule_entry_id` (int FK → ScheduleEntry), `lesson_date` (date), `is_active` (bool, default True), `created_at` (datetime), `expires_at` (datetime)
- **D-09:** `lesson_date` enables per-day attendance records for recurring weekly schedule entries.
- **D-10 (AttendanceRecord model):** `id` (int PK), `student_id` (int FK → User), `token_id` (int FK → AttendanceToken), `checked_in_at` (datetime)
- **D-11:** Unique constraint on `(student_id, token_id)` prevents duplicate check-ins.

### Claude's Discretion

- Dummy client stub form in Phase 1: whether `docker-compose.yml` references placeholder image vs minimal Python — Claude decides based on what makes `docker compose up` succeed cleanly.
- Exact `mosquitto.conf` content (anonymous access, listener port 1883) — standard config for prototype.
- `.env.example` variable names — derive from what config.py needs (SECRET_KEY, DATABASE_URL, MQTT_BROKER, MQTT_PORT, SERVER_IP, etc.).

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FOUND-01 | Project directory structure matches specification (models/, routers/, services/, templates/, static/) | D-01/D-02: Directory layout is fully specified; Python package init files required |
| FOUND-02 | `config.py` loads all settings from `.env` via pydantic-settings | pydantic-settings BaseSettings with `model_config = SettingsConfigDict(env_file=".env")` |
| FOUND-03 | `database.py` provides SQLAlchemy engine, session factory, and `Base` | SQLAlchemy 2.0 `create_engine` with `check_same_thread=False` for SQLite; `sessionmaker`; `DeclarativeBase` |
| FOUND-04 | All 5 models exist: User, Device, ScheduleEntry, AttendanceToken, AttendanceRecord | SQLAlchemy 2.0 `Mapped[]` + `mapped_column()` style; `Time` and `Date` column types for SQLite |
| FOUND-05 | `docker-compose.yml` starts server + mqtt + 3 dummy client stubs cleanly | mosquitto:2 image; dummy clients as minimal Python containers with `sleep infinity` or real stub script |
| FOUND-06 | `Dockerfile` builds a multi-arch image (linux/arm64, linux/arm/v7) | `python:3.11-slim` is multi-arch on Docker Hub; build requires `docker buildx` + QEMU binfmt_misc registration |
| FOUND-07 | `mosquitto/config/mosquitto.conf` is present and correct | Mosquitto 2.0+ requires explicit `listener 1883` + `allow_anonymous true` — no longer defaults to accepting external connections |
| FOUND-08 | `.env.example` documents all required environment variables | Derive names from config.py fields: SECRET_KEY, DATABASE_URL, MQTT_BROKER, MQTT_PORT, SERVER_IP |
</phase_requirements>

---

## Summary

This phase creates a greenfield Python/FastAPI project with no existing code to reference. The stack is fully locked by CLAUDE.md constraints: FastAPI + SQLAlchemy 2.0 + pydantic-settings + SQLite + Mosquitto + Docker Compose. The primary technical risks are (1) Docker buildx is not installed on the dev machine and must be set up to satisfy the multi-arch Dockerfile requirement, and (2) Mosquitto 2.0+ changed its defaults in a breaking way that requires explicit configuration.

SQLAlchemy 2.0 introduces a new declarative style (`DeclarativeBase` subclass + `Mapped[]` type annotations) that is the current standard. The project must use this style, not the legacy `declarative_base()` function. FastAPI lifespan context managers (replacing deprecated `@app.on_event`) are the correct pattern for running `create_all()` at startup.

For dummy clients in Phase 1, the simplest approach that makes `docker compose up` succeed cleanly is a minimal Python image running `sleep infinity` as a stub — the full dummy client logic belongs to Phase 7 (DUMMY-01 through DUMMY-07). This avoids introducing Phase 7 complexity into Phase 1.

**Primary recommendation:** Use `python:3.11-slim` as the base image (natively multi-arch on Docker Hub); use SQLAlchemy 2.0 `DeclarativeBase` + `Mapped[]` style for all models; use FastAPI `lifespan` context manager for `create_all()`; note that `docker buildx` must be installed on the dev machine before the multi-arch build can be verified.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi | 0.135.2 | ASGI web framework | Locked by CLAUDE.md; async, type-safe, built-in docs |
| uvicorn | 0.42.0 | ASGI server | Standard pairing with FastAPI |
| sqlalchemy | 2.0.48 | ORM + query engine | Locked by CLAUDE.md; 2.0 is current major, 1.x is legacy |
| pydantic-settings | 2.13.1 | Config from .env | Locked by CLAUDE.md; separate from pydantic v2 core |
| Jinja2 | 3.1.6 | HTML templating | Locked by CLAUDE.md (FastAPI Jinja2 integration) |
| python-multipart | 0.0.22 | Form parsing for FastAPI | Required for FastAPI form handling |

### Supporting (Phase 1 only needs stubs; full use in later phases)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| paho-mqtt | 2.1.0 | MQTT client | Phase 6 (server MQTT) + Phase 7 (dummy clients) |
| python-jose | 3.5.0 | JWT encode/decode | Phase 2 (authentication) |
| passlib | 1.7.4 | Password hashing (bcrypt) | Phase 2 (authentication) |
| apscheduler | 3.11.2 | Background job scheduler | Phase 6 (token issuer) |

### Docker images
| Image | Version | Purpose |
|-------|---------|---------|
| python:3.11-slim | latest 3.11 slim | App + dummy client base; natively multi-arch (amd64/arm64/arm/v7) |
| eclipse-mosquitto | 2 | MQTT broker |

### Installation (requirements.txt for Phase 1)
```
fastapi==0.135.2
uvicorn[standard]==0.42.0
sqlalchemy==2.0.48
pydantic-settings==2.13.1
jinja2==3.1.6
python-multipart==0.0.22
# Pinned for later phases — install now to avoid Docker layer rebuilds:
paho-mqtt==2.1.0
python-jose[cryptography]==3.5.0
passlib[bcrypt]==1.7.4
apscheduler==3.11.2
```

**Version verification (confirmed 2026-03-27):**
- fastapi: 0.135.2 (latest)
- sqlalchemy: 2.0.48 (latest 2.0.x)
- pydantic-settings: 2.13.1 (latest)
- uvicorn: 0.42.0 (latest)
- paho-mqtt: 2.1.0 (latest)
- python-jose: 3.5.0 (latest)
- passlib: 1.7.4 (latest — no new release since 2020, still maintained)
- apscheduler: 3.11.2 (latest 3.x)

---

## Architecture Patterns

### Recommended Project Structure
```
SmartAttend/
├── app/
│   ├── __init__.py
│   ├── main.py             # FastAPI app instance + lifespan
│   ├── config.py           # pydantic-settings Settings class
│   ├── database.py         # engine, SessionLocal, Base
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── device.py
│   │   ├── schedule_entry.py
│   │   ├── attendance_token.py
│   │   └── attendance_record.py
│   ├── routers/            # empty __init__.py only in Phase 1
│   ├── services/           # empty __init__.py only in Phase 1
│   ├── templates/          # empty dir in Phase 1
│   └── static/             # Pico CSS file goes here (Phase 2+)
├── dummy_client/
│   ├── Dockerfile          # Phase 1: python:3.11-slim stub
│   └── main.py             # Phase 1: stub (sleep loop); real impl Phase 7
├── mosquitto/
│   └── config/
│       └── mosquitto.conf
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── .env                    # not committed — gitignored
```

### Pattern 1: FastAPI Lifespan for Database Init (D-03)
**What:** Use `contextlib.asynccontextmanager` to define a lifespan function; run `create_all()` before yield.
**When to use:** Always — `@app.on_event("startup")` is deprecated since FastAPI 0.95.0.
**Example:**
```python
# Source: https://fastapi.tiangolo.com/advanced/events/
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: nothing needed for SQLite

app = FastAPI(lifespan=lifespan)
```

### Pattern 2: SQLAlchemy 2.0 Declarative Models (FOUND-04)
**What:** Subclass `DeclarativeBase` (not legacy `declarative_base()`) and use `Mapped[]` + `mapped_column()`.
**When to use:** All 5 models.
**Example:**
```python
# Source: https://docs.sqlalchemy.org/en/20/orm/declarative_styles.html
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Boolean, Integer

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    class_name: Mapped[str | None] = mapped_column(String, nullable=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
```

### Pattern 3: SQLite Time and Date column types (FOUND-04)
**What:** SQLAlchemy `Time` and `Date` types store as text in SQLite; Python `datetime.time` and `datetime.date` round-trip correctly.
**When to use:** `ScheduleEntry.start_time` / `end_time` (Time), `AttendanceToken.lesson_date` (Date).
```python
from datetime import time, date
from sqlalchemy import Time, Date

class ScheduleEntry(Base):
    __tablename__ = "schedule_entries"
    # ...
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
```

### Pattern 4: pydantic-settings Config (FOUND-02)
**What:** `BaseSettings` subclass with `SettingsConfigDict(env_file=".env")`.
**When to use:** `app/config.py` — single Settings instance, exposed via `get_settings()` with `@lru_cache`.
```python
# Source: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    secret_key: str
    database_url: str = "sqlite:///./smartattend.db"
    mqtt_broker: str = "mqtt"
    mqtt_port: int = 1883
    server_ip: str = "localhost"

    model_config = SettingsConfigDict(env_file=".env")

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### Pattern 5: SQLAlchemy Session Dependency (FOUND-03)
**What:** Synchronous `create_engine` with `check_same_thread=False` for SQLite; generator dependency for FastAPI.
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.config import get_settings

engine = create_engine(
    get_settings().database_url,
    connect_args={"check_same_thread": False},  # Required for SQLite
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Pattern 6: Mosquitto 2.0 Configuration (FOUND-07)
**What:** Mosquitto 2.0+ changed defaults — it no longer accepts external connections without explicit configuration.
**Critical change:** Without `listener 1883` + `allow_anonymous true`, the broker only accepts loopback connections from inside its own container — the FastAPI server and dummy clients cannot connect.
```ini
# mosquitto/config/mosquitto.conf
listener 1883
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest stdout
```

### Pattern 7: Docker Compose for Development Stack (FOUND-05)
**What:** Four services: `server`, `mqtt`, `client-e101`, `client-e102`, `client-e103`. Dummy clients in Phase 1 are minimal Python stubs that just stay alive.
**Phase 1 dummy client approach:** Use `python:3.11-slim` with `command: python -c "import time; time.sleep(float('inf'))"` — satisfies `docker compose up` with no errors, no exit. Real logic added in Phase 7.

### Anti-Patterns to Avoid
- **`@app.on_event("startup")`:** Deprecated since FastAPI 0.95.0. Use `lifespan` context manager.
- **`declarative_base()`:** Legacy SQLAlchemy 1.x API. Use `class Base(DeclarativeBase): pass` in SQLAlchemy 2.0.
- **Hardcoded `connect_args` for non-SQLite:** `check_same_thread` is SQLite-only; SQLAlchemy raises on other databases. Keep it inside a conditional or accept it's SQLite-only for this prototype.
- **Missing `listener` in Mosquitto config:** Mosquitto 2.0+ silently refuses external connections without it — this causes confusing "connection refused" errors from app and dummy clients.
- **`docker buildx` assumed available:** buildx is NOT installed by default on Arch Linux Docker package. Must install `docker-buildx` AUR package or use Docker Desktop.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Environment variable loading | Custom `.env` parser | pydantic-settings BaseSettings | Type coercion, validation, nested settings, secret file support |
| Database session lifecycle | Manual open/close | SQLAlchemy `sessionmaker` + generator dependency | Thread safety, rollback on exception, proper cleanup |
| Schema creation | Raw `CREATE TABLE` SQL | `Base.metadata.create_all()` | Handles FK ordering, index creation, idempotent |
| Multi-arch Docker builds | Per-arch Dockerfiles | Single Dockerfile + `docker buildx` | One manifest, automatic arch selection on pull |
| MQTT connection management | Raw socket TCP | paho-mqtt client | Reconnection, QoS, topic routing |

**Key insight:** All "infrastructure plumbing" in this phase is solved by library-level APIs. Phase 1 is about wiring them together correctly, not implementing any of them.

---

## Common Pitfalls

### Pitfall 1: Mosquitto 2.0 Default Listener
**What goes wrong:** `docker compose up` starts the broker, server logs "Connection refused" on MQTT connect, even though the `mqtt` container is running and healthy.
**Why it happens:** Mosquitto 2.0 (released 2020) changed the default to local-only mode. Without `listener 1883` in `mosquitto.conf`, it only binds to `127.0.0.1` inside the container — not accessible by other Docker services.
**How to avoid:** Always include `listener 1883` and `allow_anonymous true` in `mosquitto/config/mosquitto.conf`. Mount it as a volume in docker-compose: `./mosquitto/config:/mosquitto/config:ro`.
**Warning signs:** MQTT connect errors from server despite broker container showing `Running`.

### Pitfall 2: SQLite `check_same_thread` Missing
**What goes wrong:** `sqlalchemy.exc.ProgrammingError: SQLite objects created in a thread can only be used in that same thread`.
**Why it happens:** FastAPI uses a thread pool for sync routes; SQLite's default connection object is not thread-safe. `check_same_thread=False` disables SQLite's own check — SQLAlchemy's session management handles safety correctly.
**How to avoid:** Always pass `connect_args={"check_same_thread": False}` to `create_engine` when `DATABASE_URL` starts with `sqlite`.
**Warning signs:** Error only appears under concurrent requests, not in simple tests.

### Pitfall 3: `docker buildx` Not Installed
**What goes wrong:** `docker buildx build --platform linux/arm64,linux/arm/v7 ...` fails with `docker: unknown command: docker buildx`.
**Why it happens:** On Arch Linux, the `docker` pacman package does not include `docker-buildx`. It is a separate plugin.
**How to avoid:** Install `docker-buildx` from AUR: `yay -S docker-buildx`. Then run `docker buildx create --use` to create a builder, and register QEMU binfmt handlers with `docker run --rm --privileged multiarch/qemu-user-static --reset -p yes`.
**Warning signs:** `docker: unknown command: docker buildx` or `docker buildx ls` shows only the default builder with no arm entries.

### Pitfall 4: Models Imported Before `Base` Defined
**What goes wrong:** `create_all()` creates no tables (empty database) even though model files exist.
**Why it happens:** SQLAlchemy tracks model classes on the `Base` at import time. If model modules are never imported, SQLAlchemy's metadata has no record of them.
**How to avoid:** Import all model modules in `app/models/__init__.py` (or in `database.py` or `main.py`) before calling `create_all()`.
**Warning signs:** Database file created but empty; no `sqlite_master` rows.

### Pitfall 5: pydantic-settings v2 API Break
**What goes wrong:** `class Config: env_file = ".env"` is silently ignored (no error), settings always use defaults.
**Why it happens:** pydantic-settings v2 replaced the inner `Config` class with `model_config = SettingsConfigDict(...)`. The old inner `class Config` pattern is from pydantic v1 and has no effect in v2.
**How to avoid:** Use `model_config = SettingsConfigDict(env_file=".env")` at class level (not a nested class). Current pydantic-settings version is 2.13.1.
**Warning signs:** `.env` file present but settings use default values; no import error.

### Pitfall 6: SQLAlchemy `Time` and SQLite
**What goes wrong:** `start_time` stored as a string like `"10:30:00"` in SQLite; Python receives a `str` not `datetime.time` on read.
**Why it happens:** SQLite has no native `TIME` type; SQLAlchemy stores as string. The ORM converts on read, but only if the column type is `Time` (not `String`).
**How to avoid:** Always use `mapped_column(Time)` — not `mapped_column(String)` — for time fields. SQLAlchemy handles the conversion automatically.

---

## Code Examples

### Complete `database.py`
```python
# Pattern from SQLAlchemy 2.0 official docs
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from typing import Generator
from app.config import get_settings

class Base(DeclarativeBase):
    pass

engine = create_engine(
    get_settings().database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### `app/models/__init__.py` — ensure all models are imported for `create_all()`
```python
from app.models.user import User
from app.models.device import Device
from app.models.schedule_entry import ScheduleEntry
from app.models.attendance_token import AttendanceToken
from app.models.attendance_record import AttendanceRecord

__all__ = ["User", "Device", "ScheduleEntry", "AttendanceToken", "AttendanceRecord"]
```

### `app/main.py` skeleton
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import engine, Base
import app.models  # noqa: F401 — ensures all models registered on Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="SmartAttend", lifespan=lifespan)
```

### `mosquitto/config/mosquitto.conf`
```ini
listener 1883
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest stdout
```

### `docker-compose.yml` skeleton (Phase 1)
```yaml
version: "3.9"

services:
  server:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - mqtt
    volumes:
      - ./data:/app/data

  mqtt:
    image: eclipse-mosquitto:2
    ports:
      - "1883:1883"
    volumes:
      - ./mosquitto/config:/mosquitto/config:ro
      - mosquitto-data:/mosquitto/data

  client-e101:
    build: ./dummy_client
    environment:
      - DEVICE_ID=e101
      - ROOM=E101
      - MQTT_BROKER=mqtt
      - MQTT_PORT=1883
      - LUX_VALUE=400
    depends_on:
      - mqtt

  client-e102:
    build: ./dummy_client
    environment:
      - DEVICE_ID=e102
      - ROOM=E102
      - MQTT_BROKER=mqtt
      - MQTT_PORT=1883
      - LUX_VALUE=350
    depends_on:
      - mqtt

  client-e103:
    build: ./dummy_client
    environment:
      - DEVICE_ID=e103
      - ROOM=E103
      - MQTT_BROKER=mqtt
      - MQTT_PORT=1883
      - LUX_VALUE=500
    depends_on:
      - mqtt

volumes:
  mosquitto-data:
```

### Multi-arch Dockerfile
```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Note on multi-arch build:** `python:3.11-slim` is available for linux/amd64, linux/arm64, and linux/arm/v7 on Docker Hub — the image manifest is already multi-arch. The Dockerfile itself needs no arch-specific logic. Building the multi-arch manifest requires `docker buildx` and QEMU registration on the dev machine. The Dockerfile is correct; the build command is:
```bash
docker buildx build --platform linux/arm64,linux/arm/v7 -t smartattend:latest .
```

### Dummy client Phase 1 stub (`dummy_client/main.py`)
```python
"""Phase 1 stub — keeps container alive. Real implementation in Phase 7."""
import time
import os

device_id = os.environ.get("DEVICE_ID", "unknown")
print(f"[stub] dummy_client {device_id} running (Phase 1 placeholder)")

while True:
    time.sleep(60)
```

### Dummy client `dummy_client/Dockerfile`
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY main.py .
CMD ["python", "main.py"]
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `declarative_base()` | `class Base(DeclarativeBase): pass` | SQLAlchemy 2.0 (2023) | Legacy API deprecated; new style uses typed `Mapped[]` |
| `@app.on_event("startup")` | `@asynccontextmanager async def lifespan(app)` | FastAPI 0.95.0 (2023) | Deprecated decorator; lifespan is the standard |
| Inner `class Config` in BaseSettings | `model_config = SettingsConfigDict(...)` | pydantic-settings v2 (2023) | Silent breakage if using old pattern with v2 |
| Mosquitto default listener on all interfaces | Default local-only; must add `listener 1883` | Mosquitto 2.0 (2020) | Causes "connection refused" in Docker without explicit config |
| `Column(String, ...)` style | `mapped_column(String, ...)` with `Mapped[]` annotations | SQLAlchemy 2.0 (2023) | Old style still works but not idiomatic; new style required for type safety |

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | App development | ✓ | 3.14.3 | — |
| pip | Package install | ✓ | 26.0.1 | — |
| Docker | Container builds | ✓ | 29.3.0 (server) / 28.5.2 (client) | — |
| docker compose | Stack orchestration | ✓ | 5.1.1 | — |
| docker buildx | Multi-arch image build (FOUND-06) | ✗ | — | Install `docker-buildx` AUR package; register QEMU binfmt |
| fastapi | Already installed | ✓ | 0.135.1 | — |
| pydantic-settings | Already installed | ✓ | 2.13.1 | — |

**Missing dependencies with no fallback:**
- `docker buildx` — required to build multi-arch manifest for FOUND-06. Must install before executing the multi-arch build task. Install: `yay -S docker-buildx`, then `docker buildx create --use`, then `docker run --rm --privileged multiarch/qemu-user-static --reset -p yes`.

**Notes:**
- Python 3.14.3 is the host interpreter — this does not affect what runs inside Docker (project uses `python:3.11-slim`). Python 3.11 was chosen for maximum ARM package compatibility on PyPI.
- `docker compose` v2 (plugin, not standalone `docker-compose`) is available and is the correct version for YAML `version:` field interpretation.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (not yet installed) |
| Config file | `pytest.ini` or `pyproject.toml [tool.pytest]` — Wave 0 gap |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FOUND-01 | Directory structure has all required paths | smoke (filesystem check) | `pytest tests/test_foundation.py::test_directory_structure -x` | ❌ Wave 0 |
| FOUND-02 | Settings loads from .env without error | unit | `pytest tests/test_foundation.py::test_config_loads -x` | ❌ Wave 0 |
| FOUND-03 | `get_db()` yields a Session; `Base` has metadata | unit | `pytest tests/test_foundation.py::test_database_session -x` | ❌ Wave 0 |
| FOUND-04 | All 5 tables exist after `create_all()` | unit | `pytest tests/test_foundation.py::test_all_tables_created -x` | ❌ Wave 0 |
| FOUND-05 | `docker compose up` exits 0 and all containers healthy | integration (manual) | manual — requires Docker daemon | manual-only |
| FOUND-06 | Dockerfile builds for arm64 and arm/v7 | integration (manual) | manual — requires buildx | manual-only |
| FOUND-07 | mosquitto.conf mounts and broker accepts connections | integration (manual) | manual — requires Docker | manual-only |
| FOUND-08 | `.env.example` contains all vars referenced in config.py | smoke | `pytest tests/test_foundation.py::test_env_example_complete -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_foundation.py -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/__init__.py` — makes tests a package
- [ ] `tests/conftest.py` — shared fixtures (tmp SQLite DB, test settings override)
- [ ] `tests/test_foundation.py` — covers FOUND-01, FOUND-02, FOUND-03, FOUND-04, FOUND-08
- [ ] Framework install: `pip install pytest pytest-anyio` (anyio needed for async FastAPI tests later)

---

## Open Questions

1. **Python 3.11 vs 3.12/3.13 in Docker**
   - What we know: `python:3.11-slim` is multi-arch and widely tested on ARM; PyPI binary wheels for 3.11 are well-established.
   - What's unclear: Whether `python:3.12-slim` has equally good ARM binary wheel coverage for passlib/cryptography.
   - Recommendation: Use `python:3.11-slim` as locked — conservative choice for ARM compatibility.

2. **`docker buildx` installation on developer's Arch Linux machine**
   - What we know: `docker-buildx` is not installed; the `docker` pacman package does not include it; `~/.docker/cli-plugins/docker-buildx` is absent.
   - What's unclear: Whether this machine will be used to execute the multi-arch build, or whether it will be built in CI.
   - Recommendation: Plan the multi-arch build task as a discrete step that includes a `docker buildx` setup substep with the QEMU binfmt registration command. If the developer only needs to verify locally with `linux/amd64`, that's possible without buildx.

3. **SQLite database file location in Docker**
   - What we know: `DATABASE_URL=sqlite:///./smartattend.db` puts the file in the working directory inside the container.
   - What's unclear: Whether a named volume or bind mount should preserve the database across `docker compose down`.
   - Recommendation: Mount a `./data/` bind mount at `/app/data/` and set `DATABASE_URL=sqlite:////app/data/smartattend.db`. Include this in `.env.example`.

---

## Sources

### Primary (HIGH confidence)
- PyPI index (verified 2026-03-27) — all package versions confirmed current
- https://fastapi.tiangolo.com/advanced/events/ — lifespan context manager pattern
- https://docs.sqlalchemy.org/en/20/orm/declarative_styles.html — DeclarativeBase and Mapped[] style
- https://docs.pydantic.dev/latest/concepts/pydantic_settings/ — BaseSettings with SettingsConfigDict

### Secondary (MEDIUM confidence)
- https://docs.docker.com/build/building/multi-platform/ — multi-arch build with buildx
- https://cedalo.com/blog/mosquitto-docker-configuration-ultimate-guide/ — Mosquitto 2.0 Docker config
- https://wiki.archlinux.org/title/Docker — Arch Linux Docker package notes

### Tertiary (LOW confidence)
- WebSearch results on Mosquitto 2.0 default behavior change — confirmed by multiple sources, HIGH confidence
- WebSearch results on pydantic-settings v2 API — confirmed against official docs, HIGH confidence

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified against PyPI live index 2026-03-27
- Architecture patterns: HIGH — verified against FastAPI and SQLAlchemy official docs; patterns match library versions in use
- Pitfalls: HIGH — Mosquitto 2.0 change well-documented across multiple sources; SQLite thread safety is SQLAlchemy official guidance; buildx absence confirmed by direct shell check
- Multi-arch build: MEDIUM — `docker buildx` absent from dev machine; build procedure is well-documented but untested on this specific setup

**Research date:** 2026-03-27
**Valid until:** 2026-04-27 (stable ecosystem — 30 days)
