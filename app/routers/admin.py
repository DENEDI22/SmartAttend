"""Admin interface router: device management, user management, schedule CRUD."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.device import Device
from app.models.user import User

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
    """User management page -- placeholder, completed in Plan 03."""
    return templates.TemplateResponse(
        request=request,
        name="admin_users.html",
        context={"user": user, "users": [], "school_classes": [], "active_page": "users"},
    )
