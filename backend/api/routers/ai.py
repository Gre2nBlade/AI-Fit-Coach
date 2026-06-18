"""Роутер ИИ-тренера: вопрос → ответ от OpenRouter с учётом профиля."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.api.dependencies import get_current_user_id
from backend.services import ai_service, nutrition_service, user_service, workout_service

router = APIRouter(prefix="/api/ai", tags=["ai"])


async def _run_actions(user_id: int, actions: list[dict]) -> list[str]:
    """Исполнить действия, запрошенные ИИ. Возвращает список изменённых планов
    ('workout' / 'nutrition') для обновления на фронте."""
    updated: list[str] = []
    for act in actions:
        name = act.get("name")
        arg = (act.get("arg") or "").strip() or None
        try:
            if name == "regenerate_workout":
                await workout_service.regenerate(user_id, extra=arg)
                updated.append("workout")
            elif name == "regenerate_nutrition":
                await nutrition_service.regenerate(user_id, extra=arg)
                updated.append("nutrition")
            elif name == "nutrition_from_food":
                extra = f"Составь рацион в основном из этих продуктов: {arg}" if arg else None
                await nutrition_service.regenerate(user_id, extra=extra)
                updated.append("nutrition")
        except ai_service.AIError:
            pass  # действие не критично — основной ответ уже есть
    # убрать дубли, сохранив порядок
    return list(dict.fromkeys(updated))


class AskIn(BaseModel):
    # при наличии фото вопрос может быть пустым — спрашиваем «оцени, что на фото»
    question: str = Field(default="", max_length=2000)
    # data URL изображения (data:image/...;base64,...) — обрабатывается vision-моделью
    image: str | None = Field(default=None, max_length=8_000_000)


@router.post("/ask")
async def ask(payload: AskIn, user_id: int = Depends(get_current_user_id)) -> dict:
    if not payload.question.strip() and not payload.image:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Напишите вопрос или прикрепите фото.",
        )
    profile = await user_service.get_profile(user_id)
    try:
        result = await ai_service.chat(payload.question, profile, image=payload.image)
    except ai_service.AIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    plan_updated = await _run_actions(user_id, result.get("actions") or [])
    return {
        "answer": result["answer"],
        "suggestions": result.get("suggestions") or [],
        "plan_updated": plan_updated,
    }
