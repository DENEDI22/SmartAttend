"""Student router: attendance dashboard with summary stats and lesson history."""
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.attendance_record import AttendanceRecord
from app.models.attendance_token import AttendanceToken
from app.models.device import Device
from app.models.schedule_entry import ScheduleEntry
from app.models.system_setting import SystemSetting
from app.models.user import User

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(prefix="/student", tags=["student"])

MONTH_NAMES = {
    1: "Januar", 2: "Februar", 3: "Maerz", 4: "April",
    5: "Mai", 6: "Juni", 7: "Juli", 8: "August",
    9: "September", 10: "Oktober", 11: "November", 12: "Dezember",
}


@router.get("")
async def dashboard(
    request: Request,
    user: User = Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    """Student dashboard: attendance summary and lesson history (STUD-01, STUD-02)."""
    cutoff_date = date.today() - timedelta(days=365)
    global_threshold = int(SystemSetting.get_value(db, "late_threshold_minutes", "10"))

    # Query all tokens for lessons matching student's class, last 12 months
    rows = (
        db.query(AttendanceToken, ScheduleEntry)
        .join(ScheduleEntry, AttendanceToken.schedule_entry_id == ScheduleEntry.id)
        .filter(
            AttendanceToken.lesson_date >= cutoff_date,
            ScheduleEntry.class_name == user.class_name,
        )
        .order_by(AttendanceToken.lesson_date.desc(), ScheduleEntry.start_time.desc())
        .all()
    )

    # Deduplicate by (schedule_entry_id, lesson_date) — token rotation creates multiple tokens
    seen = set()
    lessons = []
    for token, entry in rows:
        key = (entry.id, token.lesson_date)
        if key in seen:
            continue
        seen.add(key)

        # Get all token IDs for this entry+date (token rotation)
        all_token_ids = [
            t[0] for t in db.query(AttendanceToken.id).filter(
                AttendanceToken.schedule_entry_id == entry.id,
                AttendanceToken.lesson_date == token.lesson_date,
            ).all()
        ]

        # Check if student has attendance record with any of these tokens
        record = (
            db.query(AttendanceRecord)
            .filter(
                AttendanceRecord.student_id == user.id,
                AttendanceRecord.token_id.in_(all_token_ids),
            )
            .first()
        )

        if record:
            threshold_min = entry.late_threshold_minutes if entry.late_threshold_minutes is not None else global_threshold
            lesson_start = datetime.combine(token.lesson_date, entry.start_time)
            late_cutoff = lesson_start + timedelta(minutes=threshold_min)
            if record.checked_in_at > late_cutoff:
                status = "Verspaetet"
            else:
                status = "Anwesend"
        else:
            status = "Abwesend"

        # Get room from device
        device = db.get(Device, entry.device_id)
        room = device.room if device else "\u2014"

        lessons.append({
            "date": token.lesson_date.strftime("%d.%m.%Y"),
            "class_name": entry.class_name,
            "start_time": entry.start_time.strftime("%H:%M"),
            "end_time": entry.end_time.strftime("%H:%M"),
            "room": room,
            "status": status,
            "_lesson_date": token.lesson_date,  # for grouping
        })

    # Compute summary stats
    total = len(lessons)
    attended = sum(1 for l in lessons if l["status"] == "Anwesend")
    late = sum(1 for l in lessons if l["status"] == "Verspaetet")
    missed = sum(1 for l in lessons if l["status"] == "Abwesend")
    percentage = round((attended + late) / total * 100) if total > 0 else 0

    stats = {
        "total": total,
        "attended": attended,
        "late": late,
        "missed": missed,
        "percentage": percentage,
    }

    # Group by month (already sorted by date DESC)
    groups = []
    current_month = None
    current_lessons = []
    for lesson in lessons:
        ld = lesson["_lesson_date"]
        month_key = f"{MONTH_NAMES[ld.month]} {ld.year}"
        if month_key != current_month:
            if current_month is not None:
                groups.append({"month": current_month, "lessons": current_lessons})
            current_month = month_key
            current_lessons = []
        current_lessons.append(lesson)
    if current_month is not None:
        groups.append({"month": current_month, "lessons": current_lessons})

    return templates.TemplateResponse(
        request=request,
        name="student.html",
        context={
            "stats": stats,
            "groups": groups,
            "active_page": "dashboard",
        },
    )
