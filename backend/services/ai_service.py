"""AI-сервис: формирование промптов + вызов OpenRouter через httpx (async).

Единственное место, которое знает про внешний AI-API.
Черновик: реальные промпты не проработаны, парсинг минимальный.
"""
from __future__ import annotations

import logging

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)


async def _chat(messages: list[dict], model: str | None = None) -> str:
    """Низкоуровневый вызов OpenRouter chat completions."""
    model = model or settings.ai_model
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": model, "messages": messages}

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{settings.openrouter_base_url}/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    # TODO: нормальный парсинг/валидация ответа
    return data["choices"][0]["message"]["content"]


async def generate_workout(user_profile: dict) -> str:
    """Сгенерировать тренировочный план по профилю пользователя."""
    # TODO: собрать нормальный промпт из профиля и целей
    messages = [
        {"role": "system", "content": "Ты — персональный фитнес-тренер."},
        {"role": "user", "content": f"Составь тренировку. Профиль: {user_profile}"},
    ]
    logger.info("AI: generate_workout (черновик)")
    return await _chat(messages)


async def generate_nutrition(user_profile: dict) -> str:
    """Сгенерировать план питания / советы по КБЖУ."""
    messages = [
        {"role": "system", "content": "Ты — диетолог."},
        {"role": "user", "content": f"Составь план питания. Профиль: {user_profile}"},
    ]
    logger.info("AI: generate_nutrition (черновик)")
    return await _chat(messages)
