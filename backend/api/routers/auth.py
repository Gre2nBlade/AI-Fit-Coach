"""Роутер аутентификации: регистрация и вход. Возвращает JWT."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from backend.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])

MIN_PASSWORD_LEN = 6


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LEN)
    full_name: str | None = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
async def register(payload: RegisterIn) -> dict:
    result = await auth_service.register(payload.email, payload.password, payload.full_name)
    if result is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already used")
    return result


@router.post("/login")
async def login(payload: LoginIn) -> dict:
    result = await auth_service.login(payload.email, payload.password)
    if result is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="bad credentials")
    return result
