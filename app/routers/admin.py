"""Admin interface router: device management, user management, schedule CRUD."""
import csv
import io
import json
import re
from datetime import time as dt_time

from fastapi import APIRouter, Depends, Form, Query, Request, UploadFile, File
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.device import Device
from app.models.schedule_entry import ScheduleEntry
from app.models.school_class import SchoolClass
from app.models.system_setting import SystemSetting
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
                "late_threshold_minutes": entry.late_threshold_minutes,
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


# ── User CSV Import (CSV-01, CSV-02, CSV-03) ────────────────────────


USER_CSV_HEADERS = ["email", "first_name", "last_name", "role", "class_name", "password"]


def validate_user_row(row: dict, db: Session) -> list[str]:
    """Validate a single CSV row for user import. Returns list of error strings."""
    errors = []
    # 1. Required fields
    for field in ("email", "first_name", "last_name", "role", "password"):
        if not row.get(field, "").strip():
            errors.append(f'Pflichtfeld "{field}" fehlt')
    # 2. Email format
    email = row.get("email", "").strip()
    if email and ("@" not in email or "." not in email):
        errors.append("Ungueltige E-Mail-Adresse")
    # 3. Role validation
    role = row.get("role", "").strip()
    if role and role not in ("admin", "teacher", "student"):
        errors.append("Ungueltige Rolle. Erlaubt: admin, teacher, student")
    # 4. Password length
    password = row.get("password", "").strip()
    if password and len(password) < 6:
        errors.append("Passwort zu kurz (mindestens 6 Zeichen)")
    # 5. Existing user info note (not an error)
    if email and not errors:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            errors.append("Existierender Benutzer wird aktualisiert")
    return errors


@router.get("/users/csv-template")
async def users_csv_template(user: User = Depends(require_role("admin"))):
    """Download CSV template for user import (D-01, D-02, D-04, D-14)."""
    output = io.StringIO()
    writer = csv.writer(output, delimiter=",")
    writer.writerow(USER_CSV_HEADERS)
    writer.writerow(["max.mustermann@schule.de", "Max", "Mustermann", "student", "10A", "passwort123"])
    content = output.getvalue()
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="benutzer_vorlage.csv"'},
    )


@router.post("/users/csv-upload")
async def users_csv_upload(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Upload and validate a user CSV file (D-05, D-06, D-09, D-12, D-13)."""
    raw = await file.read()

    # Size check
    if len(raw) > 1_048_576:
        return RedirectResponse(
            url="/admin/users?error=Datei+zu+gross.+Maximale+Groesse:+1+MB.",
            status_code=303,
        )

    # Decode with fallback
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))

    # Validate headers
    if reader.fieldnames is None or not all(h in reader.fieldnames for h in USER_CSV_HEADERS):
        missing = [h for h in USER_CSV_HEADERS if reader.fieldnames is None or h not in reader.fieldnames]
        return RedirectResponse(
            url=f"/admin/users?error=Fehlende+Spalten:+{',+'.join(missing)}",
            status_code=303,
        )

    rows = []
    for i, raw_row in enumerate(reader, start=2):
        # Skip blank rows
        if all(not (v or "").strip() for v in raw_row.values()):
            continue
        row_errors = validate_user_row(raw_row, db)
        is_update = any("aktualisiert" in e for e in row_errors)
        # Separate real errors from info notes
        real_errors = [e for e in row_errors if "aktualisiert" not in e]
        rows.append({
            "email": (raw_row.get("email") or "").strip(),
            "first_name": (raw_row.get("first_name") or "").strip(),
            "last_name": (raw_row.get("last_name") or "").strip(),
            "role": (raw_row.get("role") or "").strip(),
            "class_name": (raw_row.get("class_name") or "").strip(),
            "password": (raw_row.get("password") or "").strip(),
            "row_num": i,
            "errors": row_errors,
            "is_update": is_update,
        })

    if not rows:
        return RedirectResponse(
            url="/admin/users?error=Keine+Datenzeilen+gefunden.+Die+CSV-Datei+enthaelt+nur+die+Kopfzeile.",
            status_code=303,
        )

    has_errors = any(
        any("aktualisiert" not in e for e in r["errors"])
        for r in rows
    )
    error_count = sum(
        1 for r in rows
        if any("aktualisiert" not in e for e in r["errors"])
    )

    # Build rows_json without errors (re-validate on confirm)
    rows_json = json.dumps([
        {k: v for k, v in r.items() if k not in ("errors", "is_update", "row_num")}
        for r in rows
    ])

    return templates.TemplateResponse(
        request=request,
        name="admin_users_csv_preview.html",
        context={
            "user": user,
            "rows": rows,
            "has_errors": has_errors,
            "rows_json": rows_json,
            "error_count": error_count,
            "total_count": len(rows),
            "active_page": "users",
        },
    )


@router.post("/users/csv-confirm")
async def users_csv_confirm(
    rows_json: str = Form(...),
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Confirm and commit validated CSV rows with upsert (D-06, D-10)."""
    try:
        rows = json.loads(rows_json)
    except json.JSONDecodeError:
        return RedirectResponse(url="/admin/users?error=Ungueltige+Daten.", status_code=303)

    # Re-validate
    for row in rows:
        errors = validate_user_row(row, db)
        real_errors = [e for e in errors if "aktualisiert" not in e]
        if real_errors:
            return RedirectResponse(url="/admin/users?error=Validierungsfehler.", status_code=303)

    count = 0
    for row in rows:
        email = row["email"].strip()
        first_name = row["first_name"].strip()
        last_name = row["last_name"].strip()
        role = row["role"].strip()
        class_name = row.get("class_name", "").strip() or None
        password = row["password"].strip()

        existing = db.query(User).filter(User.email == email).first()
        if existing:
            existing.first_name = first_name
            existing.last_name = last_name
            existing.role = role
            existing.class_name = class_name
            existing.password_hash = get_password_hash(password)
        else:
            # Auto-create SchoolClass if needed
            if class_name:
                existing_class = db.query(SchoolClass).filter(SchoolClass.name == class_name).first()
                if not existing_class:
                    db.add(SchoolClass(name=class_name))
                    db.flush()
            new_user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=role,
                class_name=class_name,
                password_hash=get_password_hash(password),
                is_active=True,
            )
            db.add(new_user)
        count += 1

    db.commit()
    return RedirectResponse(
        url=f"/admin/users?msg={count}+Benutzer+erfolgreich+importiert.",
        status_code=303,
    )


# ── Schedule CRUD (ADMIN-07 through ADMIN-10) ──────────────────────


@router.post("/schedule/add")
async def schedule_add(
    device_id: int = Form(...),
    teacher_id: int = Form(...),
    class_name: str = Form(...),
    weekday: int = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    late_threshold_minutes: str | None = Form(None),
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Add a schedule entry with overlap detection (ADMIN-08, ADMIN-09)."""
    # Convert empty string to None for optional late threshold
    late_thresh = None
    if late_threshold_minutes and late_threshold_minutes.strip():
        late_thresh = int(late_threshold_minutes)

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
        late_threshold_minutes=late_thresh,
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


# ── Settings (LATE-01, LATE-02) ──────────────────────────────────────


@router.get("/settings")
async def settings_page(
    request: Request,
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Admin settings page with global late threshold."""
    late_threshold_minutes = SystemSetting.get_value(db, "late_threshold_minutes", "10")
    return templates.TemplateResponse(
        request=request,
        name="admin_settings.html",
        context={
            "user": user,
            "late_threshold_minutes": late_threshold_minutes,
            "active_page": "settings",
        },
    )


@router.post("/settings")
async def settings_save(
    request: Request,
    late_threshold_minutes: int = Form(...),
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Save global settings."""
    if late_threshold_minutes < 1 or late_threshold_minutes > 120:
        return RedirectResponse(
            url="/admin/settings?error=Wert+muss+zwischen+1+und+120+liegen.",
            status_code=303,
        )
    SystemSetting.set_value(db, "late_threshold_minutes", str(late_threshold_minutes))
    db.commit()
    return RedirectResponse(url="/admin/settings?msg=Einstellungen+gespeichert.", status_code=303)
