import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.core.security import (
    hash_password, verify_password, validate_password_strength,
    create_access_token, decode_access_token,
)
from app.models.user import User, PasswordHistory, RevokedToken, PasswordResetToken
from app.models.master_data import Contact
from app.models.enums import UserRole
from app.schemas.auth import SignupRequest, LoginRequest, CreateUserRequest
from app.services.audit_service import log_action


def _check_password_rules(password: str, re_password: str) -> None:
    if password != re_password:
        raise HTTPException(status_code=422, detail="Password and confirmation do not match")
    err = validate_password_strength(password)
    if err:
        raise HTTPException(status_code=422, detail=err)


def _check_unique_login_and_email(db: Session, login_id: str, email: str) -> None:
    if db.query(User).filter(User.login_id == login_id).first():
        raise HTTPException(status_code=409, detail="Login ID already exists")
    if db.query(User).filter(func.lower(User.email) == email.lower()).first():
        raise HTTPException(status_code=409, detail="Email already exists")


def _check_password_not_reused(db: Session, user_id: int, new_password: str, limit: int = 5) -> None:
    recent = (
        db.query(PasswordHistory)
        .filter(PasswordHistory.user_id == user_id)
        .order_by(PasswordHistory.created_at.desc())
        .limit(limit)
        .all()
    )
    for record in recent:
        if verify_password(new_password, record.hashed_password):
            raise HTTPException(status_code=422, detail="Password was recently used; choose a different one")


def signup(db: Session, payload: SignupRequest) -> User:
    _check_password_rules(payload.password, payload.re_password)
    _check_unique_login_and_email(db, payload.login_id, payload.email)

    contact = db.query(Contact).filter(func.lower(Contact.email) == payload.email.lower()).first()
    user = User(
        name=contact.name if contact else None,
        login_id=payload.login_id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=UserRole.USER,
        is_active=True,
        contact_id=contact.id if contact else None,
    )
    db.add(user)
    try:
        db.flush()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unable to save record. Please try again.")

    db.add(PasswordHistory(
        user_id=user.id, hashed_password=user.hashed_password,
        created_at=datetime.now(timezone.utc),
    ))
    log_action(db, user.id, "SIGNUP", "User", user.id)
    db.commit()
    db.refresh(user)
    return user


def create_user(db: Session, payload: CreateUserRequest, creator: User) -> User:
    if payload.role == UserRole.ADMINISTRATOR:
        raise HTTPException(status_code=403, detail="Administrator accounts are provisioned during system setup")
    _check_password_rules(payload.password, payload.re_password)
    _check_unique_login_and_email(db, payload.login_id, payload.email)

    # Role must be explicitly chosen by the caller (enforced by Pydantic requiring the field);
    # it is never silently defaulted to Administrator.
    contact = db.query(Contact).filter(func.lower(Contact.email) == payload.email.lower()).first()
    user = User(
        name=payload.name or (contact.name if contact else None),
        login_id=payload.login_id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=True,
        contact_id=contact.id if payload.role == UserRole.USER and contact else None,
    )
    db.add(user)
    try:
        db.flush()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unable to save record. Please try again.")

    db.add(PasswordHistory(
        user_id=user.id, hashed_password=user.hashed_password,
        created_at=datetime.now(timezone.utc),
    ))
    log_action(db, creator.id, "CREATE_USER", "User", user.id, details=f"role={payload.role.value}")
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, payload: LoginRequest) -> str:
    generic_error = HTTPException(status_code=401, detail="Invalid Login Id or Password")

    user = db.query(User).filter(User.login_id == payload.login_id).first()
    if user is None:
        # Don't reveal whether the login id or password was wrong.
        raise generic_error

    now = datetime.now(timezone.utc)
    locked_until = user.locked_until
    if locked_until is not None and locked_until.tzinfo is None:
        # SQLite (used in tests) returns naive datetimes; Postgres returns aware ones.
        locked_until = locked_until.replace(tzinfo=timezone.utc)
    if locked_until and locked_until > now:
        raise HTTPException(
            status_code=423,
            detail="Account temporarily locked due to repeated failed logins. Try again later.",
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="You do not have permission to access this page.")

    if not verify_password(payload.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
            user.locked_until = now + timedelta(minutes=settings.LOCKOUT_MINUTES)
            user.failed_login_attempts = 0
        db.commit()
        raise generic_error

    user.failed_login_attempts = 0
    user.locked_until = None
    log_action(db, user.id, "LOGIN", "User", user.id)
    db.commit()

    return create_access_token(subject=user.login_id, role=user.role.value)


def logout(db: Session, token: str) -> None:
    payload = decode_access_token(token)
    if not payload:
        return
    jti = payload.get("jti")
    exp = payload.get("exp")
    if not jti or not exp:
        return
    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
    if not db.query(RevokedToken).filter(RevokedToken.jti == jti).first():
        db.add(RevokedToken(jti=jti, revoked_at=datetime.now(timezone.utc), expires_at=expires_at))
        db.commit()


def request_password_reset(db: Session, email: str) -> None:
    """Always behaves the same way whether or not the email exists, to avoid leaking account info."""
    user = db.query(User).filter(func.lower(User.email) == email.lower()).first()
    if not user:
        return
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    reset = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        used=False,
    )
    db.add(reset)
    db.commit()
    # In production this raw_token would be emailed to the user, never returned via the API.


def reset_password(db: Session, raw_token: str, new_password: str, re_password: str) -> None:
    if new_password != re_password:
        raise HTTPException(status_code=422, detail="Password and confirmation do not match")
    err = validate_password_strength(new_password)
    if err:
        raise HTTPException(status_code=422, detail=err)

    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    reset = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == token_hash)
        .first()
    )
    now = datetime.now(timezone.utc)
    expires_at = reset.expires_at if reset else None
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if not reset or reset.used or expires_at < now:
        raise HTTPException(status_code=400, detail="Reset link is invalid or has expired")

    user = db.query(User).filter(User.id == reset.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Reset link is invalid or has expired")

    _check_password_not_reused(db, user.id, new_password)

    user.hashed_password = hash_password(new_password)
    reset.used = True
    db.add(PasswordHistory(
        user_id=user.id, hashed_password=user.hashed_password, created_at=now,
    ))
    log_action(db, user.id, "PASSWORD_RESET", "User", user.id)
    db.commit()
