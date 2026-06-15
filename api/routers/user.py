"""Роутер профиля пользователя. Вызывает services.user_service."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import get_current_user
from services import user_service

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/me")
async def me(current=Depends(get_current_user)) -> dict:
    profile = await user_service.get_or_create(
        tg_id=current["tg_id"],
        username=current["username"],
        full_name=current["full_name"],
    )
    return profile


@router.post("/profile")
async def update_profile(payload: dict, current=Depends(get_current_user)) -> dict:
    # Черновик: payload без строгой схемы. Потом — pydantic-модель.
    updated = await user_service.update_profile(current["tg_id"], **payload)
    return updated or {"error": "user not found"}
