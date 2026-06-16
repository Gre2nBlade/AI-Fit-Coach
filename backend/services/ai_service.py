"""AI-сервис: формирование промптов + вызов OpenRouter через httpx (async).

Единственное место, которое знает про внешний AI-API.
Черновик: реальные промпты не проработаны, парсинг минимальный.
"""
from __future__ import annotations

import logging

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)


class AIError(Exception):
    """Ошибка вызова AI-провайдера (для понятного ответа клиенту)."""


async def _chat(messages: list[dict], model: str | None = None) -> str:
    """Низкоуровневый вызов OpenRouter chat completions."""
    if not settings.openrouter_api_key or settings.openrouter_api_key.startswith("PUT_"):
        raise AIError("AI не настроен: задайте OPENROUTER_API_KEY в .env")

    model = model or settings.ai_model
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": model, "messages": messages}

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{settings.openrouter_base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        logger.warning("OpenRouter HTTP %s: %s", e.response.status_code, e.response.text[:300])
        raise AIError("AI-провайдер вернул ошибку, попробуйте позже") from e
    except (httpx.HTTPError, KeyError, IndexError) as e:
        logger.warning("OpenRouter error: %s", e)
        raise AIError("Не удалось получить ответ от AI") from e


def _profile_context(profile: dict | None) -> str:
    """Краткая сводка о пользователе для системного промпта."""
    if not profile:
        return ""
    m = profile.get("metrics") or {}
    parts = [
        f"Имя: {profile.get('full_name') or '—'}",
        f"Пол: {profile.get('sex') or '—'}",
        f"Возраст: {profile.get('age') or '—'}",
        f"Рост: {profile.get('height_cm') or '—'} см",
        f"Вес: {profile.get('weight_kg') or '—'} кг",
        f"Цель: {profile.get('goal') or '—'}",
        f"Уровень: {profile.get('level') or '—'}",
        f"Место: {profile.get('place') or '—'}",
    ]
    if m:
        parts.append(f"Норма калорий: {m.get('calories')} ккал")
        parts.append(f"КБЖУ: Б{m.get('protein_g')}/Ж{m.get('fat_g')}/У{m.get('carbs_g')} г")
    return "; ".join(parts)


async def chat(question: str, profile: dict | None = None) -> str:
    """Ответ ИИ-тренера на вопрос пользователя с учётом его профиля."""
    system = (
        "Ты — персональный ИИ фитнес-тренер AI Fit Coach. Отвечай кратко, "
        "по делу, дружелюбно и на русском. Давай практичные советы по тренировкам, "
        "питанию и восстановлению."
    )
    ctx = _profile_context(profile)
    if ctx:
        system += f"\n\nДанные пользователя: {ctx}"

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": question},
    ]
    return await _chat(messages)


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
