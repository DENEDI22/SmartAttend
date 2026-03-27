from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import engine, Base
import app.models  # noqa: F401 — registers all model classes on Base metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup. Nothing to clean up for SQLite."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="SmartAttend",
    description="NFC-based attendance tracking system",
    version="0.1.0",
    lifespan=lifespan,
)
