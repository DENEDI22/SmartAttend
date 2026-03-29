"""Admin interface router: device management, user management, schedule CRUD."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
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
    """Device management page -- placeholder, completed in Plan 02."""
    return templates.TemplateResponse(
        request=request,
        name="admin_devices.html",
        context={"user": user, "devices": [], "active_page": "devices"},
    )


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
