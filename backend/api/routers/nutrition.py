"""Роутер питания. Вызывает services.nutrition_service."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_current_user_id
from backend.services import nutrition_service

router = APIRouter(prefix="/api/nutrition", tags=["nutrition"])


@router.get("/diary")
async def diary(user_id: int = Depends(get_current_user_id)) -> list[dict]:
    return await nutrition_service.get_diary(user_id)


@router.post("/food")
async def add_food(payload: dict, user_id: int = Depends(get_current_user_id)) -> dict:
    return await nutrition_service.add_food(user_id, **payload)
