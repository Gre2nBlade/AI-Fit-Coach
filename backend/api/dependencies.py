"""FastAPI-зависимости. Аутентификация по JWT (Bearer-токен).

get_current_user_id извлекает user_id из заголовка Authorization: Bearer <token>.
Используется как Depends во всех защищённых роутерах.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.services import auth_service

_bearer = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> int:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="no token")

    user_id = auth_service.decode_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="bad token")

    return user_id


async def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> bool:
    """Гард админ-роутеров: пропускает только валидный токен с role=admin."""
    if credentials is None or not auth_service.is_admin_token(credentials.credentials):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="admin only")
    return True
