from datetime import datetime
from sqlalchemy import Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    token_id: Mapped[int] = mapped_column(Integer, ForeignKey("attendance_tokens.id"), nullable=False)
    checked_in_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint("student_id", "token_id", name="uq_student_token"),  # D-11: prevents duplicate check-ins
    )
