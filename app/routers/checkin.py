"""Student check-in router: NFC token → attendance record."""
from datetime import datetime

from fastapi import APIRouter, Cookie, Depends, Form, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.dependencies import require_role
from app.models.attendance_record import AttendanceRecord
from app.models.attendance_token import AttendanceToken
from app.models.device import Device
from app.models.schedule_entry import ScheduleEntry
from app.models.user import User
from app.services.auth import ALGORITHM

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()


def _get_user_from_cookie(access_token: str | None, db: Session) -> User | None:
    """Like get_current_user but returns None instead of raising."""
    if access_token is None:
        return None
    try:
        payload = jwt.decode(access_token, get_settings().secret_key, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    user = db.get(User, int(user_id))
    if user is None or not user.is_active:
        return None
    return user


def _validate_token(token: str | None, db: Session):
    """Return (AttendanceToken, error_message) tuple."""
    if not token:
        return None, "Ungültiger oder fehlender Token."
    db_token = db.query(AttendanceToken).filter(AttendanceToken.token == token).first()
    if db_token is None:
        return None, "Ungültiger oder fehlender Token."
    if not db_token.is_active:
        return None, "Dieser Token ist nicht mehr gültig."
    if datetime.now() > db_token.expires_at:
        return None, "Diese Stunde ist bereits beendet."
    return db_token, None


@router.get("/checkin")
async def checkin_page(
    request: Request,
    token: str = Query(default=""),
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    """GET /checkin — show check-in form or error page."""
    # No token at all
    if not token:
        return templates.TemplateResponse(
            request=request,
            name="checkin.html",
            context={"error": "Ungültiger oder fehlender Token."},
        )

    # Manual auth check — redirect to login preserving token
    user = _get_user_from_cookie(access_token, db)
    if user is None:
        return RedirectResponse(
            url=f"/login?next=/checkin?token={token}",
            status_code=303,
        )

    # Role check
    if user.role != "student":
        return templates.TemplateResponse(
            request=request,
            name="checkin.html",
            context={"error": "Nur Schüler können sich einchecken."},
        )

    # Validate the attendance token
    db_token, error = _validate_token(token, db)
    if error:
        return templates.TemplateResponse(
            request=request,
            name="checkin.html",
            context={"error": error},
        )

    # Verify student is enrolled in the class this token belongs to
    entry = db.get(ScheduleEntry, db_token.schedule_entry_id)
    device = db.get(Device, db_token.device_id)
    if entry and user.class_name != entry.class_name:
        return templates.TemplateResponse(
            request=request,
            name="checkin.html",
            context={"error": "Sie gehören nicht zu dieser Klasse."},
        )

    # Check for existing record across ALL tokens for this lesson + date
    # (tokens rotate every minute, so student may have used an earlier one)
    all_token_ids = [
        t[0] for t in db.query(AttendanceToken.id).filter(
            AttendanceToken.schedule_entry_id == db_token.schedule_entry_id,
            AttendanceToken.lesson_date == db_token.lesson_date,
        ).all()
    ]
    existing = db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == user.id,
        AttendanceRecord.token_id.in_(all_token_ids),
    ).first()
    if existing:
        return templates.TemplateResponse(
            request=request,
            name="checkin.html",
            context={
                "already_checked_in": True,
                "checked_in_time": existing.checked_in_at.strftime("%H:%M"),
                "room": device.room if device and device.room else "Unbekannt",
                "start_time": entry.start_time.strftime("%H:%M") if entry else "",
                "end_time": entry.end_time.strftime("%H:%M") if entry else "",
            },
        )
    return templates.TemplateResponse(
        request=request,
        name="checkin.html",
        context={
            "room": device.room if device and device.room else "Unbekannt",
            "start_time": entry.start_time.strftime("%H:%M") if entry else "",
            "end_time": entry.end_time.strftime("%H:%M") if entry else "",
            "token": token,
        },
    )


@router.post("/checkin")
async def checkin_confirm(
    request: Request,
    token: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("student")),
):
    """POST /checkin — confirm attendance, write record."""
    # Validate the attendance token
    db_token, error = _validate_token(token, db)
    if error:
        return templates.TemplateResponse(
            request=request,
            name="checkin.html",
            context={"error": error},
        )

    # Verify student is enrolled in the class this token belongs to
    entry = db.get(ScheduleEntry, db_token.schedule_entry_id)
    if entry and user.class_name != entry.class_name:
        return templates.TemplateResponse(
            request=request,
            name="checkin.html",
            context={"error": "Sie gehören nicht zu dieser Klasse."},
        )

    # Check for duplicate across ALL tokens for this lesson + date
    all_token_ids = [
        t[0] for t in db.query(AttendanceToken.id).filter(
            AttendanceToken.schedule_entry_id == db_token.schedule_entry_id,
            AttendanceToken.lesson_date == db_token.lesson_date,
        ).all()
    ]
    existing = db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == user.id,
        AttendanceRecord.token_id.in_(all_token_ids),
    ).first()
    if existing:
        device = db.get(Device, db_token.device_id)
        return templates.TemplateResponse(
            request=request,
            name="checkin.html",
            context={
                "already_checked_in": True,
                "checked_in_time": existing.checked_in_at.strftime("%H:%M"),
                "room": device.room if device and device.room else "Unbekannt",
                "start_time": entry.start_time.strftime("%H:%M") if entry else "",
                "end_time": entry.end_time.strftime("%H:%M") if entry else "",
            },
        )

    # Create attendance record
    record = AttendanceRecord(
        student_id=user.id,
        token_id=db_token.id,
        checked_in_at=datetime.now(),
    )
    try:
        db.add(record)
        db.commit()
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="checkin.html",
            context={"error": "Sie haben sich bereits eingecheckt."},
        )

    return templates.TemplateResponse(
        request=request,
        name="checkin.html",
        context={"success": True},
    )
