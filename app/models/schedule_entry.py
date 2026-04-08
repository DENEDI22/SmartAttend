from datetime import time
from sqlalchemy import Integer, String, ForeignKey, Time
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class ScheduleEntry(Base):
    __tablename__ = "schedule_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(Integer, ForeignKey("devices.id"), nullable=False)
    teacher_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    class_name: Mapped[str] = mapped_column(String, nullable=False)  # e.g. "10A"
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)     # 0=Monday ... 6=Sunday
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    late_threshold_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
