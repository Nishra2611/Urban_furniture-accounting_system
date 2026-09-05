from typing import Iterable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, RevokedToken
from app.models.enums import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    jti = payload.get("jti")
    if jti and db.query(RevokedToken).filter(RevokedToken.jti == jti).first():
        raise HTTPException(status_code=401, detail="Session has expired. Please log in again.")

    login_id = payload.get("sub")
    if login_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.login_id == login_id).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_roles(*roles: UserRole):
    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this page.",
            )
        return user
    return _checker


require_admin = require_roles(UserRole.ADMINISTRATOR)
require_accountant_or_admin = require_roles(UserRole.ACCOUNTANT, UserRole.ADMINISTRATOR)
require_any_role = require_roles(UserRole.USER, UserRole.ACCOUNTANT, UserRole.ADMINISTRATOR)
