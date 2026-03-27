from datetime import datetime
from sqlalchemy import String, Boolean, Integer, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)  # MQTT client identifier
    room: Mapped[str | None] = mapped_column(String, nullable=True)
    label: Mapped[str | None] = mapped_column(String, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # admin-controlled
    is_online: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)   # heartbeat-controlled
    last_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_lux: Mapped[float | None] = mapped_column(Float, nullable=True)
