"""Роутер тренировок. Вызывает services.workout_service."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import get_current_user
from services import workout_service

router = APIRouter(prefix="/api/workout", tags=["workout"])


@router.get("/plans")
async def list_plans(current=Depends(get_current_user)) -> list[dict]:
    return await workout_service.list_plans(current["tg_id"])


@router.post("/generate")
async def generate(current=Depends(get_current_user)) -> dict:
    plan = await workout_service.create_plan_for(current["tg_id"])
    return plan or {"error": "user not found"}
