"""Admin interface router: device management, user management, schedule CRUD."""
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.device import Device
from app.models.school_class import SchoolClass
from app.models.user import User
from app.services.auth import get_password_hash

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/admin", tags=["admin"])


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
    """Device management page with inline-editable table (ADMIN-01)."""
    devices = db.query(Device).order_by(Device.device_id).all()
    return templates.TemplateResponse(
        request=request,
        name="admin_devices.html",
        context={"user": user, "devices": devices, "active_page": "devices"},
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
