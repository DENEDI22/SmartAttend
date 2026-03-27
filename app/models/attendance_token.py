from datetime import date, datetime
from sqlalchemy import Integer, String, Boolean, ForeignKey, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class AttendanceToken(Base):
    __tablename__ = "attendance_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)  # UUID string
    device_id: Mapped[int] = mapped_column(Integer, ForeignKey("devices.id"), nullable=False)
    schedule_entry_id: Mapped[int] = mapped_column(Integer, ForeignKey("schedule_entries.id"), nullable=False)
    lesson_date: Mapped[date] = mapped_column(Date, nullable=False)  # specific calendar date (D-09)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
