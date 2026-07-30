from fastapi import (APIRouter, Depends, HTTPException, Request, Response, status)
from pwdlib import PasswordHash
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db, User
from app.config import settings
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from datetime import datetime, timedelta, UTC

import jwt
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

router = APIRouter(prefix="/api/auth", tags=["auth"])
password_hash = PasswordHash.recommended()
DbSession = Annotated[Session, Depends(get_db)]

bearer = HTTPBearer(auto_error=False)
JWT_ISSUER = "dialog-api"
JWT_AUDIENCE = "dialog-web"

def create_token(user_id: int) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
            "iss": JWT_ISSUER,
            "aud": JWT_AUDIENCE
        },
        settings.jwt_secret_key,
        algorithm="HS256"
    )

def read_token(token: str) -> int | None:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=["HS256"],
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE
        )
    except jwt.PyJWTError:
        return None

    user_id = payload.get("sub")
    return int(user_id) if isinstance(user_id, str) and user_id.isdigit() else None

def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        "dialog_access_token",
        token,
        max_age=settings.jwt_expire_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/"
    )

def get_current_user(
        request: Request, 
        db: DbSession, 
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
        token = credentials.credentials if credentials else request.cookies.get("dialog_access_token")
        user_id = read_token(token) if token else None
        user = db.get(User, user_id) if user_id else None

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Требуется вход"
            )
        return user

CurrentUser = Annotated[User, Depends(get_current_user)]
        

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    created_at: datetime

class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if len(value) < 2:
            raise ValueError("Имя должно содержать не менее 2 символов")
        return value

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)

def register(payload: RegisterRequest, response: Response, db: DbSession):
    user = User(
        name=payload.name, 
        email=str(payload.email).lower(),
        password_hash=password_hash.hash(payload.password))

    db.add(user)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует"
        ) from exc

    token = create_token(user.id)
    set_auth_cookie(response, token)

    return AuthResponse(access_token=token, user=user)

@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, db: DbSession) -> AuthResponse:
    email = str(payload.email).lower()
    user = db.scalar(select(User).where(User.email == email))

    if not user or not password_hash.verify(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется вход"
        )
    token = create_token(user.id)
    set_auth_cookie(response, token)

    return AuthResponse(access_token=token, user=user)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie("dialog_access_token", poth="/")

@router.get("/me", response_model=UserResponse)
def me(user: CurrentUser) -> User:
    return user