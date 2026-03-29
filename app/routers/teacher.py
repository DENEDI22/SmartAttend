"""Teacher router: dashboard, lesson detail, CSV export."""
from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.attendance_record import AttendanceRecord
from app.models.attendance_token import AttendanceToken
from app.models.device import Device
from app.models.schedule_entry import ScheduleEntry
from app.models.user import User

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(prefix="/teacher", tags=["teacher"])

WEEKDAY_NAMES = [
    "Montag", "Dienstag", "Mittwoch", "Donnerstag",
    "Freitag", "Samstag", "Sonntag",
]


@router.get("")
async def dashboard(
    request: Request,
    user: User = Depends(require_role("teacher")),
    db: Session = Depends(get_db),
):
    """Teacher dashboard: today's lessons with attendance counts (D-01, D-02, D-03, D-04)."""
    today = date.today()
    weekday = today.weekday()

    # Query today's lessons for this teacher, ordered by start time
    entries = (
        db.query(ScheduleEntry)
        .filter(
            ScheduleEntry.teacher_id == user.id,
            ScheduleEntry.weekday == weekday,
        )
        .order_by(ScheduleEntry.start_time)
        .all()
    )

    lessons = []
    for entry in entries:
        # Get room from Device (ScheduleEntry has no room field)
        device = db.get(Device, entry.device_id)
        room = device.room if device else "—"

        # Check for today's token
        token = (
            db.query(AttendanceToken)
            .filter(
                AttendanceToken.schedule_entry_id == entry.id,
                AttendanceToken.lesson_date == today,
            )
            .first()
        )

        # Count expected students (active students with matching class_name)
        expected = (
            db.query(User)
            .filter(
                User.role == "student",
                User.class_name == entry.class_name,
                User.is_active == True,  # noqa: E712
            )
            .count()
        )

        # Count checked-in students
        checked_in = 0
        token_id = None
        if token is not None:
            checked_in = (
                db.query(AttendanceRecord)
                .filter(AttendanceRecord.token_id == token.id)
                .count()
            )
            token_id = token.id

        lessons.append({
            "class_name": entry.class_name,
            "room": room,
            "start_time": entry.start_time.strftime("%H:%M"),
            "end_time": entry.end_time.strftime("%H:%M"),
            "expected": expected,
            "checked_in": checked_in,
            "token_id": token_id,
        })

    weekday_name = WEEKDAY_NAMES[weekday]
    today_str = today.strftime("%d.%m.%Y")

    return templates.TemplateResponse(
        request=request,
        name="teacher_dashboard.html",
        context={
            "lessons": lessons,
            "weekday_name": weekday_name,
            "today_str": today_str,
            "active_page": "overview",
        },
    )
