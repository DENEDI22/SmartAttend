"""FastAPI dependencies: current user extraction and role enforcement."""
from fastapi import Cookie, Depends, HTTPException
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.services.auth import ALGORITHM


async def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    """Decode the access_token cookie and return the authenticated User.

    D-07: No cookie or invalid JWT → 303 redirect to /login (not 401).
    D-11: This dependency only checks authentication. Role checking is in require_role().
    """
    if access_token is None:
        raise HTTPException(
            status_code=303,
            headers={"Location": "/login"},
        )
    try:
        payload = jwt.decode(
            access_token,
            get_settings().secret_key,
            algorithms=[ALGORITHM],
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=303,
                headers={"Location": "/login"},
            )
    except JWTError:
        # Covers ExpiredSignatureError and all other JWT failures (Pitfall 5)
        raise HTTPException(
            status_code=303,
            headers={"Location": "/login"},
        )
    user = db.get(User, int(user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=303,
            headers={"Location": "/login"},
        )
    return user


def require_role(*roles: str):
    """Return a FastAPI dependency that checks the current user's role.

    D-11: Wrong role → 403 (not redirect). Correct role → returns User ORM object.

    Usage:
        @router.get("/admin")
        async def admin_page(user: User = Depends(require_role("admin"))):
            ...
    """
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=403,
                detail="Keine Berechtigung.",
            )
        return user
    return role_checker
