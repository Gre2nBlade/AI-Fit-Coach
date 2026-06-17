"""Роутер прогресса: ежедневный чек-ин и агрегаты для графиков."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.api.dependencies import get_current_user_id
from backend.services import progress_service

router = APIRouter(prefix="/api/progress", tags=["progress"])


class CheckinIn(BaseModel):
    ate_well: bool = False
    trained: bool = False
    all_done: bool = False


@router.get("/today")
async def today(user_id: int = Depends(get_current_user_id)) -> dict:
    return await progress_service.get_today(user_id)


@router.post("/checkin")
async def checkin(payload: CheckinIn, user_id: int = Depends(get_current_user_id)) -> dict:
    return await progress_service.set_checkin(
        user_id, payload.ate_well, payload.trained, payload.all_done
    )


@router.get("/summary")
async def summary(user_id: int = Depends(get_current_user_id)) -> dict:
    return await progress_service.get_summary(user_id)
