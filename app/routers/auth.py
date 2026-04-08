"""Authentication router: login, logout, /auth/me, /student landing."""
from datetime import timedelta

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.services.auth import authenticate_user, create_access_token

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()


@router.get("/login")
async def login_page(request: Request, next: str = ""):
    """Render login form. Passes next param into template for ?next= threading (D-09)."""
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"next": next, "error": None},
    )


@router.post("/auth/login")
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form(default=""),
    db: Session = Depends(get_db),
):
    """Process login form.

    D-05: Re-render on failure (no redirect).
    D-06: Error messages in German.
    D-08/D-09/D-10: Role-based redirect; ?next= only for students.
    D-04: HTTP-only cookie, samesite=lax, secure=False.
    Anti-pattern: set_cookie() called on the RedirectResponse instance we return.
    """
    # Look up by email — D-01
    user = db.query(User).filter(User.email == email).first()

    if user is None or not authenticate_user(db, email, password):
        # Distinguish "user not found / wrong password" from "inactive"
        if user is not None and not user.is_active:
            error_msg = "Dieses Konto ist deaktiviert."
        else:
            error_msg = "Ungültige E-Mail oder Passwort."
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"next": next, "error": error_msg},
            status_code=200,
        )

    # Determine expiry by role — D-03
    if user.role == "student":
        expires = timedelta(days=30)
    else:
        expires = timedelta(hours=8)

    token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=expires,
    )

    # Role-based redirect — D-08, D-09, D-10
    if user.role == "admin":
        redirect_url = "/admin"
    elif user.role == "teacher":
        redirect_url = "/teacher"
    else:  # student
        # D-09/D-10: ?next= only for students; validate it's a relative path (Pitfall 2)
        if next and next.startswith("/") and "://" not in next:
            redirect_url = next
        else:
            redirect_url = "/student"

    response = RedirectResponse(url=redirect_url, status_code=303)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,              # D-04: HTTP-only RPi deployment
        max_age=int(expires.total_seconds()),
    )
    return response


@router.post("/auth/logout")
async def logout():
    """Clear the access_token cookie and redirect to /login — AUTH-04."""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="access_token")
    return response


@router.get("/auth/me")
async def me(user: User = Depends(get_current_user)):
    """Return current user info as JSON — AUTH-05.

    Returns 303 to /login if not authenticated (via get_current_user dependency).
    """
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }


@router.get("/student")
async def student_landing(
    request: Request,
    user: User = Depends(require_role("student")),
):
    """Student placeholder landing page — D-09. Full check-in is Phase 5."""
    return templates.TemplateResponse(
        request=request,
        name="student.html",
        context={},
    )


# Test-only route for require_role integration tests — AUTH-06
# This route is harmless in production (admin dashboard is Phase 3)
@router.get("/auth/admin-only-test")
async def admin_only_test(user: User = Depends(require_role("admin"))):
    """Exists only to test require_role('admin') in integration tests."""
    return {"ok": True, "role": user.role}
