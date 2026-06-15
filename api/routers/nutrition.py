"""Роутер питания. Вызывает services.nutrition_service."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import get_current_user
from services import nutrition_service

router = APIRouter(prefix="/api/nutrition", tags=["nutrition"])


@router.get("/diary")
async def diary(current=Depends(get_current_user)) -> list[dict]:
    return await nutrition_service.get_diary(current["tg_id"])


@router.post("/food")
async def add_food(payload: dict, current=Depends(get_current_user)) -> dict:
    entry = await nutrition_service.add_food(current["tg_id"], **payload)
    return entry or {"error": "user not found"}
