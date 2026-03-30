"""Teacher router: dashboard, lesson detail, CSV export."""
import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, Response
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

        # Count checked-in students (across ALL tokens for this entry + date,
        # since scheduler rotates tokens every minute)
        checked_in = 0
        token_id = None
        if token is not None:
            all_token_ids = (
                db.query(AttendanceToken.id)
                .filter(
                    AttendanceToken.schedule_entry_id == entry.id,
                    AttendanceToken.lesson_date == today,
                )
                .all()
            )
            t_ids = [t[0] for t in all_token_ids]
            if t_ids:
                checked_in = (
                    db.query(AttendanceRecord.student_id)
                    .filter(AttendanceRecord.token_id.in_(t_ids))
                    .distinct()
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


def _build_roster(db: Session, schedule_entry: ScheduleEntry, token: AttendanceToken | None):
    """Build full class roster with present/absent status.

    Queries attendance records across ALL tokens for this schedule entry + date,
    not just the current active token. This is necessary because the scheduler
    rotates tokens every minute, so students may have checked in with an earlier token.

    Returns (roster_list, checked_in_count, expected_count).
    """
    # All active students in this class, sorted by last name then first name
    students = (
        db.query(User)
        .filter(
            User.role == "student",
            User.class_name == schedule_entry.class_name,
            User.is_active == True,  # noqa: E712
        )
        .order_by(User.last_name, User.first_name)
        .all()
    )

    # Build attendance lookup across ALL tokens for this schedule entry + date
    records_by_student: dict[int, AttendanceRecord] = {}
    if token is not None:
        all_token_ids = (
            db.query(AttendanceToken.id)
            .filter(
                AttendanceToken.schedule_entry_id == schedule_entry.id,
                AttendanceToken.lesson_date == token.lesson_date,
            )
            .all()
        )
        token_ids = [t[0] for t in all_token_ids]
        if token_ids:
            records = (
                db.query(AttendanceRecord)
                .filter(AttendanceRecord.token_id.in_(token_ids))
                .all()
            )
            # Keep the earliest record per student (first check-in)
            for r in records:
                if r.student_id not in records_by_student:
                    records_by_student[r.student_id] = r

    roster = []
    checked_in = 0
    for student in students:
        record = records_by_student.get(student.id)
        if record:
            status = "Anwesend"
            time_str = record.checked_in_at.strftime("%H:%M")
            checked_in += 1
        else:
            status = "Abwesend"
            time_str = ""
        roster.append({
            "last_name": student.last_name,
            "first_name": student.first_name,
            "status": status,
            "time": time_str,
        })

    return roster, checked_in, len(students)


@router.get("/lesson/{token_id}")
async def lesson_detail(
    request: Request,
    token_id: int,
    user: User = Depends(require_role("teacher")),
    db: Session = Depends(get_db),
):
    """Lesson attendance roster (TEACH-03): full class with present/absent status."""
    # Look up token
    token = db.get(AttendanceToken, token_id)
    if token is None:
        return RedirectResponse(url="/teacher?error=Stunde+nicht+gefunden.", status_code=303)

    # Look up schedule entry and verify ownership
    schedule_entry = db.get(ScheduleEntry, token.schedule_entry_id)
    if schedule_entry is None or schedule_entry.teacher_id != user.id:
        return RedirectResponse(
            url="/teacher?error=Sie+haben+keinen+Zugriff+auf+diese+Stunde.",
            status_code=303,
        )

    # Get room from device
    device = db.get(Device, schedule_entry.device_id)
    room = device.room if device else "—"

    roster, checked_in, expected = _build_roster(db, schedule_entry, token)

    return templates.TemplateResponse(
        request=request,
        name="teacher_lesson.html",
        context={
            "roster": roster,
            "class_name": schedule_entry.class_name,
            "room": room,
            "start_time": schedule_entry.start_time.strftime("%H:%M"),
            "end_time": schedule_entry.end_time.strftime("%H:%M"),
            "checked_in": checked_in,
            "expected": expected,
            "token_id": token_id,
            "active_page": "overview",
        },
    )


@router.get("/lesson/{token_id}/csv")
async def lesson_csv(
    token_id: int,
    user: User = Depends(require_role("teacher")),
    db: Session = Depends(get_db),
):
    """CSV export of lesson attendance (TEACH-04): semicolons, UTF-8 BOM, German filename."""
    # Look up token
    token = db.get(AttendanceToken, token_id)
    if token is None:
        return RedirectResponse(url="/teacher?error=Stunde+nicht+gefunden.", status_code=303)

    # Look up schedule entry and verify ownership
    schedule_entry = db.get(ScheduleEntry, token.schedule_entry_id)
    if schedule_entry is None or schedule_entry.teacher_id != user.id:
        return RedirectResponse(
            url="/teacher?error=Sie+haben+keinen+Zugriff+auf+diese+Stunde.",
            status_code=303,
        )

    roster, _checked_in, _expected = _build_roster(db, schedule_entry, token)

    # Build CSV with UTF-8 BOM and semicolon delimiter
    output = io.StringIO()
    output.write("\ufeff")  # UTF-8 BOM
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Nachname", "Vorname", "Klasse", "Status", "Uhrzeit"])
    for row in roster:
        writer.writerow([
            row["last_name"],
            row["first_name"],
            schedule_entry.class_name,
            row["status"],
            row["time"],
        ])

    filename = f"Anwesenheit_{schedule_entry.class_name}_{token.lesson_date.strftime('%Y-%m-%d')}.csv"

    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
