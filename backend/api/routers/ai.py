"""Роутер ИИ-тренера: вопрос → ответ от OpenRouter с учётом профиля."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.api.dependencies import get_current_user_id
from backend.services import ai_service, user_service

router = APIRouter(prefix="/api/ai", tags=["ai"])


class AskIn(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


@router.post("/ask")
async def ask(payload: AskIn, user_id: int = Depends(get_current_user_id)) -> dict:
    profile = await user_service.get_profile(user_id)
    try:
        answer = await ai_service.chat(payload.question, profile)
    except ai_service.AIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    return {"answer": answer}
