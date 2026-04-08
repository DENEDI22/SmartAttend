"""Admin interface router: device management, user management, schedule CRUD."""
from datetime import time as dt_time

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.device import Device
from app.models.schedule_entry import ScheduleEntry
from app.models.school_class import SchoolClass
from app.models.user import User
from app.services.auth import get_password_hash

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/admin", tags=["admin"])

WEEKDAY_NAMES = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


def check_schedule_conflict(
    db: Session,
    device_id: int,
    weekday: int,
    start_time: dt_time,
    end_time: dt_time,
    exclude_id: int | None = None,
) -> ScheduleEntry | None:
    """Check for overlapping schedule entries. Two ranges [s1,e1) and [s2,e2) overlap iff s1 < e2 AND s2 < e1."""
    query = db.query(ScheduleEntry).filter(
        ScheduleEntry.device_id == device_id,
        ScheduleEntry.weekday == weekday,
        ScheduleEntry.start_time < end_time,
        ScheduleEntry.end_time > start_time,
    )
    if exclude_id:
        query = query.filter(ScheduleEntry.id != exclude_id)
    return query.first()


@router.get("")
async def admin_root(user: User = Depends(require_role("admin"))):
    """Redirect /admin to /admin/devices (primary admin page)."""
    return RedirectResponse(url="/admin/devices", status_code=303)


@router.get("/devices")
async def devices_page(
    request: Request,
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Device management page with inline-editable table and schedule sections (ADMIN-01, ADMIN-07)."""
    devices = db.query(Device).order_by(Device.device_id).all()
    # Build schedule data per device
    device_schedules = {}
    for device in devices:
        entries = (
            db.query(ScheduleEntry)
            .filter(ScheduleEntry.device_id == device.id)
            .order_by(ScheduleEntry.weekday, ScheduleEntry.start_time)
            .all()
        )
        # Attach teacher names
        enriched = []
        for entry in entries:
            teacher = db.query(User).filter(User.id == entry.teacher_id).first()
            enriched.append({
                "id": entry.id,
                "class_name": entry.class_name,
                "teacher_name": f"{teacher.first_name} {teacher.last_name}" if teacher else "\u2014",
                "weekday": entry.weekday,
                "weekday_name": WEEKDAY_NAMES[entry.weekday] if 0 <= entry.weekday <= 6 else str(entry.weekday),
                "start_time": entry.start_time.strftime("%H:%M"),
                "end_time": entry.end_time.strftime("%H:%M"),
            })
        device_schedules[device.id] = enriched

    teachers = db.query(User).filter(User.role == "teacher").order_by(User.last_name).all()
    school_classes = db.query(SchoolClass).order_by(SchoolClass.name).all()

    return templates.TemplateResponse(
        request=request,
        name="admin_devices.html",
        context={
            "user": user,
            "devices": devices,
            "device_schedules": device_schedules,
            "teachers": teachers,
            "school_classes": school_classes,
            "weekday_names": WEEKDAY_NAMES,
            "active_page": "devices",
        },
    )


@router.post("/devices/update")
async def devices_update(
    request: Request,
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Bulk save room/label from inline-edit form (ADMIN-02).

    Form sends room_{device.id} and label_{device.id} for each device.
    """
    form = await request.form()
    devices = db.query(Device).all()
    for device in devices:
        room_key = f"room_{device.id}"
        label_key = f"label_{device.id}"
        if room_key in form:
            device.room = form[room_key] or None
        if label_key in form:
            device.label = form[label_key] or None
    db.commit()
    return RedirectResponse(url="/admin/devices?msg=Erfolgreich+aktualisiert.", status_code=303)


@router.post("/devices/{device_id}/toggle")
async def device_toggle(
    device_id: int,
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Toggle is_enabled for a single device (ADMIN-03)."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        return RedirectResponse(url="/admin/devices?error=Gerät+nicht+gefunden.", status_code=303)
    device.is_enabled = not device.is_enabled
    new_status = device.is_enabled
    db.commit()
    status = "aktiviert" if new_status else "deaktiviert"
    return RedirectResponse(url=f"/admin/devices?msg=Gerät+{status}.", status_code=303)


@router.get("/users")
async def users_page(
    request: Request,
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """User management page with user table and create form."""
    users = db.query(User).order_by(User.last_name, User.first_name).all()
    school_classes = db.query(SchoolClass).order_by(SchoolClass.name).all()
    return templates.TemplateResponse(
        request=request,
        name="admin_users.html",
        context={
            "user": user,
            "users": users,
            "school_classes": school_classes,
            "active_page": "users",
        },
    )


@router.post("/users/create")
async def users_create(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    class_name: str = Form(default=""),
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Create a new user with hashed password (ADMIN-05)."""
    # Check email uniqueness
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return RedirectResponse(
            url="/admin/users?error=E-Mail+existiert+bereits.",
            status_code=303,
        )

    # Validate role
    if role not in ("admin", "teacher", "student"):
        return RedirectResponse(
            url="/admin/users?error=Ung%C3%BCltige+Rolle.",
            status_code=303,
        )

    # Auto-create SchoolClass if new class_name provided (per D-14)
    final_class_name = class_name.strip() if class_name else None
    if final_class_name:
        existing_class = db.query(SchoolClass).filter(SchoolClass.name == final_class_name).first()
        if not existing_class:
            db.add(SchoolClass(name=final_class_name))
            db.flush()

    new_user = User(
        email=email.strip(),
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        role=role,
        class_name=final_class_name,
        password_hash=get_password_hash(password),
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/admin/users?msg=Erfolgreich+erstellt.", status_code=303)


@router.post("/users/{user_id}/deactivate")
async def user_deactivate(
    user_id: int,
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Deactivate a user (soft delete) -- sets is_active=False (ADMIN-06)."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        return RedirectResponse(url="/admin/users?error=Benutzer+nicht+gefunden.", status_code=303)
    target.is_active = False
    db.commit()
    return RedirectResponse(url="/admin/users?msg=Benutzer+deaktiviert.", status_code=303)


@router.post("/users/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    new_password: str = Form(...),
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Reset a user's password (admin only) -- PWD-02."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        return RedirectResponse(
            url="/admin/users?error=Benutzer+nicht+gefunden.",
            status_code=303,
        )
    if len(new_password) < 8:
        return RedirectResponse(
            url="/admin/users?error=Neues+Passwort+muss+mindestens+8+Zeichen+lang+sein.",
            status_code=303,
        )
    target.password_hash = get_password_hash(new_password)
    db.commit()
    return RedirectResponse(
        url=f"/admin/users?msg=Passwort+fuer+{target.first_name}+{target.last_name}+zurueckgesetzt.",
        status_code=303,
    )


@router.post("/users/update")
async def users_update(
    request: Request,
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Bulk update inline-edited user fields (name, class, role) per D-09."""
    form = await request.form()
    users = db.query(User).all()
    for u in users:
        fn_key = f"first_name_{u.id}"
        ln_key = f"last_name_{u.id}"
        cn_key = f"class_name_{u.id}"
        role_key = f"role_{u.id}"
        if fn_key in form:
            u.first_name = form[fn_key].strip()
        if ln_key in form:
            u.last_name = form[ln_key].strip()
        if cn_key in form:
            val = form[cn_key].strip()
            u.class_name = val if val else None
            # Auto-create SchoolClass if needed
            if val:
                existing_class = db.query(SchoolClass).filter(SchoolClass.name == val).first()
                if not existing_class:
                    db.add(SchoolClass(name=val))
                    db.flush()
        if role_key in form and form[role_key] in ("admin", "teacher", "student"):
            u.role = form[role_key]
    db.commit()
    return RedirectResponse(url="/admin/users?msg=Erfolgreich+aktualisiert.", status_code=303)


# ── Schedule CRUD (ADMIN-07 through ADMIN-10) ──────────────────────


@router.post("/schedule/add")
async def schedule_add(
    device_id: int = Form(...),
    teacher_id: int = Form(...),
    class_name: str = Form(...),
    weekday: int = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Add a schedule entry with overlap detection (ADMIN-08, ADMIN-09)."""
    st = dt_time.fromisoformat(start_time)
    et = dt_time.fromisoformat(end_time)

    if st >= et:
        return RedirectResponse(
            url="/admin/devices?error=Startzeit+muss+vor+Endzeit+liegen.",
            status_code=303,
        )

    # Check conflict (ADMIN-09)
    conflict = check_schedule_conflict(db, device_id, weekday, st, et)
    if conflict:
        teacher = db.query(User).filter(User.id == conflict.teacher_id).first()
        day_name = WEEKDAY_NAMES[conflict.weekday] if 0 <= conflict.weekday <= 6 else str(conflict.weekday)
        msg = (
            f"Zeitkonflikt: Ger\u00e4t ist bereits belegt am {day_name} "
            f"{conflict.start_time.strftime('%H:%M')}-{conflict.end_time.strftime('%H:%M')} "
            f"(Klasse {conflict.class_name})."
        )
        return RedirectResponse(
            url=f"/admin/devices?error={msg.replace(' ', '+')}",
            status_code=303,
        )

    # Auto-create SchoolClass if needed (per D-14)
    class_name_clean = class_name.strip()
    existing_class = db.query(SchoolClass).filter(SchoolClass.name == class_name_clean).first()
    if not existing_class:
        db.add(SchoolClass(name=class_name_clean))
        db.flush()

    entry = ScheduleEntry(
        device_id=device_id,
        teacher_id=teacher_id,
        class_name=class_name_clean,
        weekday=weekday,
        start_time=st,
        end_time=et,
    )
    db.add(entry)
    db.commit()
    return RedirectResponse(url="/admin/devices?msg=Eintrag+hinzugef%C3%BCgt.", status_code=303)


@router.post("/schedule/{entry_id}/delete")
async def schedule_delete(
    entry_id: int,
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Delete a schedule entry (ADMIN-10)."""
    entry = db.query(ScheduleEntry).filter(ScheduleEntry.id == entry_id).first()
    if not entry:
        return RedirectResponse(url="/admin/devices?error=Eintrag+nicht+gefunden.", status_code=303)
    db.delete(entry)
    db.commit()
    return RedirectResponse(url="/admin/devices?msg=Erfolgreich+gel%C3%B6scht.", status_code=303)


@router.get("/api/schedule/check-conflict")
async def api_check_conflict(
    device_id: int = Query(...),
    weekday: int = Query(...),
    start_time: str = Query(...),
    end_time: str = Query(...),
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """JSON API for JS conflict validation (D-17)."""
    st = dt_time.fromisoformat(start_time)
    et = dt_time.fromisoformat(end_time)
    conflict = check_schedule_conflict(db, device_id, weekday, st, et)
    if conflict:
        day_name = WEEKDAY_NAMES[conflict.weekday] if 0 <= conflict.weekday <= 6 else str(conflict.weekday)
        return {
            "conflict": True,
            "message": (
                f"Zeitkonflikt: Ger\u00e4t ist bereits belegt am {day_name} "
                f"{conflict.start_time.strftime('%H:%M')}-{conflict.end_time.strftime('%H:%M')} "
                f"(Klasse {conflict.class_name})."
            ),
        }
    return {"conflict": False}
