"""AI-сервис: формирование промптов + вызов OpenRouter через httpx (async).

Единственное место, которое знает про внешний AI-API.

Две модели:
  - settings.ai_model        — текстовые ответы и генерация планов (JSON);
  - settings.ai_vision_model — анализ фото в чате (multimodal).

Бесплатные модели иногда отдают невалидный JSON и отвечают небыстро, поэтому
парсинг устойчивый (вырезаем ```-блоки, ищем JSON), а при сбое отдаём фолбэк-план.
"""
from __future__ import annotations

import json
import logging
import re

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
        async with httpx.AsyncClient(timeout=90) as client:
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
        f"Желаемый вес: {profile.get('goal_weight_kg') or '—'} кг",
        f"Цель: {profile.get('goal') or '—'}",
        f"Уровень: {profile.get('level') or '—'}",
        f"Место: {profile.get('place') or '—'}",
        f"Дни тренировок: {profile.get('training_days') or '—'}",
    ]
    if m:
        parts.append(f"Норма калорий: {m.get('calories')} ккал")
        parts.append(f"КБЖУ: Б{m.get('protein_g')}/Ж{m.get('fat_g')}/У{m.get('carbs_g')} г")
        parts.append(f"Вода: {m.get('water_l')} л")
    return "; ".join(parts)


def _extract_json(text: str):
    """Достать JSON из ответа модели: убрать ```json-обёртку, найти первый объект.

    Возвращает разобранный объект/список или бросает ValueError.
    """
    if not text:
        raise ValueError("пустой ответ")
    cleaned = text.strip()
    # вырезать markdown-обёртку ```json ... ```
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # фолбэк: вытащить самую большую {...}-скобку
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError("в ответе нет валидного JSON")


# ============================================================
#  Чат ИИ-тренера (текст или текст+фото)
# ============================================================

async def chat(question: str, profile: dict | None = None, image: str | None = None) -> str:
    """Ответ ИИ-тренера. Если передано изображение (data URL/base64) —
    используется vision-модель, иначе основная текстовая."""
    system = (
        "Ты — персональный ИИ фитнес-тренер AI Fit Coach. Отвечай кратко, "
        "по делу, дружелюбно и на русском. Давай практичные советы по тренировкам, "
        "питанию и восстановлению. Если на фото еда — оцени, насколько она подходит "
        "под цель пользователя, и предложи улучшения."
    )
    ctx = _profile_context(profile)
    if ctx:
        system += f"\n\nДанные пользователя: {ctx}"

    if image:
        # multimodal-сообщение для vision-модели
        user_content = [
            {"type": "text", "text": question or "Оцени, что на фото."},
            {"type": "image_url", "image_url": {"url": image}},
        ]
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ]
        return await _chat(messages, model=settings.ai_vision_model)

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": question},
    ]
    return await _chat(messages)


# ============================================================
#  Генерация плана тренировок (структурированный JSON)
# ============================================================

# Части тела, под каждую — отдельная тренировка.
WORKOUT_GROUPS = ["Грудь", "Спина", "Ноги", "Руки"]


async def generate_workout_plan(profile: dict) -> dict:
    """Сгенерировать структурированный план тренировок по профилю.

    Возвращает dict вида:
      {"groups": [{"group","title","minutes","calories",
                   "exercises":[{"name","sets","reps","rest","difficulty"}]}]}
    При сбое ИИ — фолбэк-план (чтобы UI не оставался пустым).
    """
    ctx = _profile_context(profile)
    level = (profile.get("level") or "Начальный")
    place = (profile.get("place") or "Дома")

    system = (
        "Ты — опытный фитнес-тренер. Составь недельную программу тренировок, "
        "по одной тренировке на каждую группу мышц: Грудь, Спина, Ноги, Руки. "
        "Подбирай упражнения строго под уровень и место занятий пользователя: "
        "для начинающих — простые, но эффективные базовые упражнения с малым риском травм. "
        "Отвечай ТОЛЬКО валидным JSON без пояснений и без markdown."
    )
    schema_hint = (
        '{"groups":[{"group":"Грудь","title":"Грудь и трицепс","minutes":50,'
        '"calories":380,"exercises":[{"name":"Жим штанги лёжа","sets":4,"reps":"10",'
        '"rest":"2 мин","difficulty":"easy|medium|hard"}]}]} '
        "difficulty только из значений: easy, medium, hard. "
        "Группы строго: Грудь, Спина, Ноги, Руки. 4–6 упражнений на группу."
    )
    user = (
        f"Профиль: {ctx}\nУровень: {level}. Место: {place}.\n"
        f"Верни JSON по форме: {schema_hint}"
    )

    try:
        raw = await _chat([
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ])
        data = _extract_json(raw)
        groups = data.get("groups") if isinstance(data, dict) else None
        if not groups:
            raise ValueError("нет groups в ответе")
        return {"groups": groups}
    except (AIError, ValueError, KeyError, TypeError) as e:
        logger.warning("generate_workout_plan фолбэк: %s", e)
        return _fallback_workout(level)


def _fallback_workout(level: str) -> dict:
    """Минимальный план на случай недоступности ИИ."""
    diff = "easy" if str(level).lower().startswith("нач") else "medium"
    base = {
        "Грудь": ["Отжимания от пола", "Жим гантелей лёжа", "Разводка гантелей", "Отжимания узким хватом"],
        "Спина": ["Подтягивания/тяга резины", "Тяга гантели в наклоне", "Гиперэкстензия", "Тяга к поясу"],
        "Ноги": ["Приседания", "Выпады", "Подъём на носки", "Ягодичный мостик"],
        "Руки": ["Подъём гантелей на бицепс", "Французский жим", "Молотки", "Разгибания на трицепс"],
    }
    titles = {"Грудь": "Грудь и трицепс", "Спина": "Спина", "Ноги": "Ноги", "Руки": "Руки и плечи"}
    groups = []
    for g in WORKOUT_GROUPS:
        groups.append({
            "group": g,
            "title": titles[g],
            "minutes": 45,
            "calories": 300,
            "exercises": [
                {"name": n, "sets": 3, "reps": "12", "rest": "1 мин", "difficulty": diff}
                for n in base[g]
            ],
        })
    return {"groups": groups, "fallback": True}


# ============================================================
#  Генерация плана питания (структурированный JSON)
# ============================================================

async def generate_nutrition_plan(profile: dict) -> dict:
    """Сгенерировать план питания на день под целевые калории/КБЖУ.

    Возвращает: {"meals":[{"meal","dish","kcal"}], "target_calories": int}
    При сбое ИИ — фолбэк.
    """
    ctx = _profile_context(profile)
    m = profile.get("metrics") or {}
    target = m.get("calories")

    system = (
        "Ты — диетолог. Составь сбалансированный рацион на день под цель пользователя. "
        "Учитывай целевые калории и КБЖУ. "
        "Отвечай ТОЛЬКО валидным JSON без пояснений и без markdown."
    )
    schema_hint = (
        '{"meals":[{"meal":"Завтрак","dish":"Овсянка, яйца и банан","kcal":480},'
        '{"meal":"Обед","dish":"...","kcal":620},{"meal":"Перекус","dish":"...","kcal":220},'
        '{"meal":"Ужин","dish":"...","kcal":460}]} '
        "Приёмы пищи: Завтрак, Обед, Перекус, Ужин. Сумма kcal близка к целевым калориям."
    )
    user = (
        f"Профиль: {ctx}\nЦелевые калории: {target}.\n"
        f"Верни JSON по форме: {schema_hint}"
    )

    try:
        raw = await _chat([
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ])
        data = _extract_json(raw)
        meals = data.get("meals") if isinstance(data, dict) else None
        if not meals:
            raise ValueError("нет meals в ответе")
        return {"meals": meals, "target_calories": target}
    except (AIError, ValueError, KeyError, TypeError) as e:
        logger.warning("generate_nutrition_plan фолбэк: %s", e)
        return _fallback_nutrition(target)


def _fallback_nutrition(target) -> dict:
    return {
        "meals": [
            {"meal": "Завтрак", "dish": "Овсянка на молоке, яйца, банан", "kcal": 480},
            {"meal": "Обед", "dish": "Куриная грудка, рис, овощи", "kcal": 620},
            {"meal": "Перекус", "dish": "Творог с орехами", "kcal": 220},
            {"meal": "Ужин", "dish": "Запечённая рыба, картофель, салат", "kcal": 460},
        ],
        "target_calories": target,
        "fallback": True,
    }
