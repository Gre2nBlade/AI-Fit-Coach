"""Роутер профиля пользователя. Вызывает services.user_service."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_current_user_id
from backend.services import user_service

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/me")
async def me(user_id: int = Depends(get_current_user_id)) -> dict:
    profile = await user_service.get_profile(user_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return profile


@router.post("/profile")
async def update_profile(payload: dict, user_id: int = Depends(get_current_user_id)) -> dict:
    # Черновик: payload без строгой схемы, сервис фильтрует разрешённые поля.
    try:
        updated = await user_service.update_profile(user_id, **payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return updated
