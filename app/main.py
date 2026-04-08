import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app.models.user import User
from app.services.auth import get_password_hash
from app.services.mqtt import start_mqtt, stop_mqtt
from app.services.scheduler import start_scheduler, stop_scheduler
from app.config import get_settings
import app.models  # noqa: F401 — registers all model classes on Base metadata


async def _seed_admin(db: Session) -> None:
    """Create admin account on first boot if ADMIN_EMAIL + ADMIN_PASSWORD are set.

    D-13: Idempotent — no-op if any admin already exists.
    """
    settings = get_settings()
    if not settings.admin_email or not settings.admin_password:
        return
    existing = db.query(User).filter(User.role == "admin").first()
    if existing:
        return
    db.add(User(
        email=settings.admin_email,
        first_name="Admin",
        last_name="Admin",
        role="admin",
        password_hash=get_password_hash(settings.admin_password),
        is_active=True,
    ))
    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables, seed admin, start MQTT and scheduler on startup."""
    Base.metadata.create_all(bind=engine)
    # Migrate: add late_threshold_minutes if missing (added in phase-12)
    from sqlalchemy import inspect, text
    insp = inspect(engine)
    cols = [c["name"] for c in insp.get_columns("schedule_entries")]
    if "late_threshold_minutes" not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE schedule_entries ADD COLUMN late_threshold_minutes INTEGER"))
    db = SessionLocal()
    try:
        await _seed_admin(db)
    finally:
        db.close()

    start_mqtt()
    start_scheduler()
    yield
    stop_scheduler()
    stop_mqtt()


app = FastAPI(
    title="SmartAttend",
    description="NFC-based attendance tracking system",
    version="0.1.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

from app.routers.auth import router as auth_router  # noqa: E402
from app.routers.teacher import router as teacher_router  # noqa: E402
from app.routers.student import router as student_router  # noqa: E402
app.include_router(auth_router)
app.include_router(teacher_router)
app.include_router(student_router)

from app.routers.admin import router as admin_router  # noqa: E402
app.include_router(admin_router)

from app.routers.checkin import router as checkin_router  # noqa: E402
app.include_router(checkin_router)
