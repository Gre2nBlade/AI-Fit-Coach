"""Роутер питания. Вызывает services.nutrition_service."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_current_user_id
from backend.services import nutrition_service

router = APIRouter(prefix="/api/nutrition", tags=["nutrition"])


@router.get("/plan")
async def get_plan(user_id: int = Depends(get_current_user_id)) -> dict:
    """Текущий ИИ-план питания (генерируется при отсутствии)."""
    plan = await nutrition_service.get_plan(user_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return plan


@router.post("/regenerate")
async def regenerate(user_id: int = Depends(get_current_user_id)) -> dict:
    """Принудительно пересоздать план питания через ИИ."""
    plan = await nutrition_service.get_plan(user_id, force=True)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return plan


@router.get("/diary")
async def diary(user_id: int = Depends(get_current_user_id)) -> list[dict]:
    return await nutrition_service.get_diary(user_id)


@router.post("/food")
async def add_food(payload: dict, user_id: int = Depends(get_current_user_id)) -> dict:
    return await nutrition_service.add_food(user_id, **payload)
