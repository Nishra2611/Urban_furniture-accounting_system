"""Password hashing, JWT creation/verification, and login-lockout helpers."""
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

PASSWORD_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[^A-Za-z0-9])(?=.*[0-9]|.*[^A-Za-z0-9]).{9,}$"
)
# Rule: >8 chars (i.e. >=9), at least one lower, one upper, one special char.
_SPECIAL_RE = re.compile(r"[^A-Za-z0-9]")
_LOWER_RE = re.compile(r"[a-z]")
_UPPER_RE = re.compile(r"[A-Z]")


def validate_password_strength(password: str) -> Optional[str]:
    if len(password) <= 8:
        return "Password must be more than 8 characters"
    if not _LOWER_RE.search(password):
        return "Password must contain a lowercase character"
    if not _UPPER_RE.search(password):
        return "Password must contain an uppercase character"
    if not _SPECIAL_RE.search(password):
        return "Password must contain a special character"
    return None


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, role: str, expires_minutes: Optional[int] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode = {
        "sub": subject,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
