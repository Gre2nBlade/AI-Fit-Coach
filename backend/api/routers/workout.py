"""Роутер тренировок. Вызывает services.workout_service."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_current_user_id
from backend.services import workout_service

router = APIRouter(prefix="/api/workout", tags=["workout"])


@router.get("/plans")
async def list_plans(user_id: int = Depends(get_current_user_id)) -> list[dict]:
    return await workout_service.list_plans(user_id)


@router.post("/generate")
async def generate(user_id: int = Depends(get_current_user_id)) -> dict:
    plan = await workout_service.create_plan_for(user_id)
    return plan or {"error": "user not found"}
