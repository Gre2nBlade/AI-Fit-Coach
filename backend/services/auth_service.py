"""Аутентификация: хеширование паролей (bcrypt) + JWT (выдача/проверка).

Регистрация/логин по email + пароль. JWT.subject = id пользователя (строкой).
Не знает ни про HTTP, ни про конкретный фреймворк — чистая логика.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from backend.config import settings
from backend.db.engine import async_session_factory
from backend.db.repositories import user_repo


def hash_password(password: str) -> str:
    # bcrypt не принимает строки длиннее 72 байт — обрезаем, чтобы не падать.
    pw = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    pw = password.encode("utf-8")[:72]
    try:
        return bcrypt.checkpw(pw, password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> int | None:
    """Вернуть user_id из валидного ПОЛЬЗОВАТЕЛЬСКОГО токена или None.

    Админский токен (role=admin) не считается пользовательским — вернёт None.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
    if payload.get("role") == "admin":
        return None
    sub = payload.get("sub")
    try:
        return int(sub) if sub is not None else None
    except (TypeError, ValueError):
        return None


def create_admin_token() -> str:
    """JWT для админ-панели. Отличается от пользовательского claim'ом role=admin."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": "admin", "role": "admin", "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def is_admin_token(token: str) -> bool:
    """True, если токен валиден и имеет role=admin."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return False
    return payload.get("role") == "admin"


async def register(email: str, password: str, full_name: str | None = None) -> dict | None:
    """Создать пользователя. Возвращает {token, user} или None, если email занят."""
    async with async_session_factory() as session:
        if await user_repo.get_by_email(session, email):
            return None
        user = await user_repo.create(
            session, email=email, password_hash=hash_password(password), full_name=full_name,
        )
        return {"token": create_access_token(user.id), "user_id": user.id, "email": user.email}


async def login(email: str, password: str) -> dict | None:
    """Проверить пароль. Возвращает {token, user_id} или None."""
    async with async_session_factory() as session:
        user = await user_repo.get_by_email(session, email)
        if user is None or not verify_password(password, user.password_hash):
            return None
        return {"token": create_access_token(user.id), "user_id": user.id, "email": user.email}
