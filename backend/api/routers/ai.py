"""Роутер ИИ-тренера: вопрос → ответ от OpenRouter с учётом профиля."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.api.dependencies import get_current_user_id
from backend.services import ai_service, nutrition_service, user_service, workout_service

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _planned_kinds(actions: list[dict]) -> list[str]:
    """Какие планы ИИ собирается изменить ('workout'/'nutrition'), без выполнения.

    Нужно, чтобы вернуть фронту список планов сразу, а саму (медленную)
    ре-генерацию выполнить в фоне.
    """
    updated: list[str] = []
    for act in actions:
        name = act.get("name")
        if name == "regenerate_workout":
            updated.append("workout")
        elif name in ("regenerate_nutrition", "nutrition_from_food"):
            updated.append("nutrition")
    return list(dict.fromkeys(updated))


async def _run_actions(user_id: int, actions: list[dict]) -> None:
    """Исполнить действия, запрошенные ИИ (ре-генерация планов). Запускается в фоне."""
    for act in actions:
        name = act.get("name")
        arg = (act.get("arg") or "").strip() or None
        try:
            if name == "regenerate_workout":
                await workout_service.regenerate(user_id, extra=arg)
            elif name == "regenerate_nutrition":
                await nutrition_service.regenerate(user_id, extra=arg)
            elif name == "nutrition_from_food":
                extra = f"Составь рацион в основном из этих продуктов: {arg}" if arg else None
                await nutrition_service.regenerate(user_id, extra=extra)
        except ai_service.AIError:
            pass  # действие не критично — основной ответ уже есть


class AskIn(BaseModel):
    # при наличии фото вопрос может быть пустым — спрашиваем «оцени, что на фото»
    question: str = Field(default="", max_length=2000)
    # data URL изображения (data:image/...;base64,...) — обрабатывается vision-моделью
    image: str | None = Field(default=None, max_length=8_000_000)


@router.post("/ask")
async def ask(
    payload: AskIn,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
) -> dict:
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

    # Ответ возвращаем сразу; медленную ре-генерацию планов делаем в фоне,
    # а фронту сообщаем, какие планы скоро обновятся (plan_updated).
    actions = result.get("actions") or []
    plan_updated = _planned_kinds(actions)
    if actions:
        background_tasks.add_task(_run_actions, user_id, actions)
    return {
        "answer": result["answer"],
        "suggestions": result.get("suggestions") or [],
        "plan_updated": plan_updated,
    }
