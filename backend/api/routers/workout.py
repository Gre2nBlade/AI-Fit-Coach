"""Роутер тренировок. Вызывает services.workout_service."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_current_user_id
from backend.services import workout_service

router = APIRouter(prefix="/api/workout", tags=["workout"])


@router.get("/plan")
async def get_plan(user_id: int = Depends(get_current_user_id)) -> dict:
    """Текущий ИИ-план тренировок (генерируется при отсутствии)."""
    plan = await workout_service.get_plan(user_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return plan


@router.post("/regenerate")
async def regenerate(user_id: int = Depends(get_current_user_id)) -> dict:
    """Принудительно пересоздать план тренировок через ИИ."""
    plan = await workout_service.get_plan(user_id, force=True)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return plan


@router.get("/plans")
async def list_plans(user_id: int = Depends(get_current_user_id)) -> list[dict]:
    return await workout_service.list_plans(user_id)
