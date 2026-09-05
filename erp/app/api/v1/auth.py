from fastapi import APIRouter, Depends, HTTPException
# from fastapi.security import OAuth2PasswordBearer
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user, require_admin
from app.schemas.auth import (
    SignupRequest, LoginRequest, TokenResponse, UserOut, CreateUserRequest,
    ForgotPasswordRequest, ResetPasswordRequest,
)
from app.services import auth_service
from app.models.user import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
oauth2_scheme = HTTPBearer()


@router.post("/signup", response_model=UserOut, status_code=201)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    user = auth_service.signup(db, payload)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    token = auth_service.authenticate(db, payload)
    user = db.query(User).filter(User.login_id == payload.login_id).first()
    return TokenResponse(access_token=token, role=user.role)


# @router.post("/logout", status_code=204)
# def logout(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
#     auth_service.logout(db, token)
#     return None

@router.post("/logout", status_code=204)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    auth_service.logout(db, token)
    return None


@router.post("/create-user", response_model=UserOut, status_code=201)
def create_user(
    payload: CreateUserRequest,
    db: Session = Depends(get_db),
    creator: User = Depends(require_admin),
):
    return auth_service.create_user(db, payload, creator)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return db.query(User).all()


@router.post("/forgot-password", status_code=204)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    auth_service.request_password_reset(db, payload.email)
    return None


@router.post("/reset-password", status_code=204)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    auth_service.reset_password(db, payload.token, payload.new_password, payload.re_password)
    return None
