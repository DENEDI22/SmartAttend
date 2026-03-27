"""Authentication service: password hashing, JWT creation, user lookup."""
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.user import User

ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _truncate(password: str) -> str:
    return password.encode()[:72].decode("utf-8", errors="ignore")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Timing-safe bcrypt comparison via passlib."""
    return pwd_context.verify(_truncate(plain_password), hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a plain-text password with bcrypt."""
    return pwd_context.hash(_truncate(password))


def create_access_token(data: dict, expires_delta: timedelta) -> str:
    """Create a signed HS256 JWT with an exp claim.

    The JWT payload includes all keys from `data` plus `exp`.
    Caller is responsible for passing the correct expires_delta (8h or 1h).
    """
    payload = {**data, "exp": datetime.now(timezone.utc) + expires_delta}
    return jwt.encode(payload, get_settings().secret_key, algorithm=ALGORITHM)


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Return User if credentials are valid and account is active, else None.

    Returns None (not raises) for:
    - Email not found
    - Wrong password
    - is_active=False
    """
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user
