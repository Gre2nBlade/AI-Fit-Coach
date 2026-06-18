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
import time

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
    has_image = any(isinstance(m.get("content"), list) for m in messages)
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": model, "messages": messages}

    logger.info("OpenRouter → model=%s image=%s", model, has_image)
    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(
                f"{settings.openrouter_base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
        content = data["choices"][0]["message"]["content"]
        logger.info(
            "OpenRouter ✓ model=%s image=%s %.1fс chars=%d",
            model, has_image, time.perf_counter() - t0, len(content or ""),
        )
        return content
    except httpx.HTTPStatusError as e:
        logger.warning(
            "OpenRouter HTTP %s (%.1fс): %s",
            e.response.status_code, time.perf_counter() - t0, e.response.text[:300],
        )
        raise AIError("AI-провайдер вернул ошибку, попробуйте позже") from e
    except (httpx.HTTPError, KeyError, IndexError) as e:
        logger.warning("OpenRouter error (%.1fс): %s", time.perf_counter() - t0, e)
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
#  Фильтр запросов — держим чат в рамках фитнеса/питания/здоровья
# ============================================================

# Грубый офф-топик: явные попытки увести ассистента в программирование,
# генерацию кода/ботов и прочие не-фитнес задачи. Это первая дешёвая линия;
# вторая — строгий system-prompt и инструкция модели отказывать не по теме.
_OFFTOPIC_PATTERNS = [
    r"\bнапиши\s+(?:код|программ|скрипт|бот[ауе]?|функци)",
    r"\bсгенерируй\s+(?:код|программ|скрипт|бот)",
    r"\bтелеграм[- ]?бот|\btelegram\s*bot|\bтг[- ]?бот",
    r"\bpython\b|\bjavascript\b|\bjava\b|\bc\+\+|\bsql\b|\bhtml\b|\breact\b",
    r"\bнапиши\s+(?:письмо|статью|реферат|сочинение|стих|эссе|пост)\b",
    r"\bреши\s+(?:уравнение|задачу по|пример по)\b",
    r"\bпереведи\s+(?:текст|на\s+\w+)",
    r"\bкак\s+взломать|\bобойти\s+защиту|\bвзлом\b",
]
_OFFTOPIC_RE = re.compile("|".join(_OFFTOPIC_PATTERNS), re.IGNORECASE)

_REFUSAL = (
    "Я — фитнес-тренер AI Fit Coach и помогаю только с тренировками, питанием, "
    "здоровьем и формой. С этим вопросом помочь не смогу — спроси меня про "
    "упражнения, КБЖУ, восстановление или режим. 💪"
)


def is_offtopic(question: str) -> bool:
    """Быстрая проверка: явно не про фитнес/питание/здоровье."""
    return bool(question and _OFFTOPIC_RE.search(question))


# ============================================================
#  Действия, которые ИИ может запросить директивами в ответе
# ============================================================
#
# Свободные модели плохо поддерживают нативный tool-calling (особенно vision),
# поэтому используем простой протокол: модель в КОНЦЕ ответа может добавить
# строки-директивы, которые мы вырезаем из видимого текста и исполняем:
#
#   [[ACTION:regenerate_workout|пожелание]]   — пересоздать план тренировок
#   [[ACTION:regenerate_nutrition|пожелание]] — пересоздать план питания
#   [[ACTION:nutrition_from_food|список продуктов]] — рацион из этих продуктов
#   [[SUGGEST:вопрос1|вопрос2|вопрос3]]        — контекстные подсказки
#
_ACTION_RE = re.compile(r"\[\[ACTION:([a-z_]+)(?:\|(.*?))?\]\]", re.IGNORECASE | re.DOTALL)
_SUGGEST_RE = re.compile(r"\[\[SUGGEST:(.*?)\]\]", re.IGNORECASE | re.DOTALL)


def parse_directives(text: str) -> tuple[str, list[dict], list[str]]:
    """Разобрать ответ модели: вернуть (чистый_текст, действия, подсказки)."""
    actions = [
        {"name": m.group(1).lower(), "arg": (m.group(2) or "").strip()}
        for m in _ACTION_RE.finditer(text or "")
    ]
    suggests: list[str] = []
    sm = _SUGGEST_RE.search(text or "")
    if sm:
        suggests = [s.strip() for s in sm.group(1).split("|") if s.strip()][:3]
    clean = _ACTION_RE.sub("", text or "")
    clean = _SUGGEST_RE.sub("", clean).strip()
    return clean, actions, suggests


# ============================================================
#  Чат ИИ-тренера (текст или текст+фото)
# ============================================================

_CHAT_SYSTEM = (
    "Ты — персональный ИИ фитнес-тренер AI Fit Coach. Отвечай кратко, по делу, "
    "дружелюбно и на русском. Помогай ТОЛЬКО с темами фитнеса: тренировки, "
    "упражнения, питание, КБЖУ, восстановление, сон, мотивация, здоровье и форма тела. "
    "Если вопрос НЕ про это (код, программирование, боты, общие знания и т.п.) — "
    "вежливо откажись и верни разговор к фитнесу, ничего лишнего не делай.\n\n"
    "Ты можешь менять планы пользователя. Если просят изменить/пересоздать тренировки "
    "или питание, либо если по фото видно продукты/холодильник — В КОНЦЕ ответа добавь "
    "СЛУЖЕБНУЮ строку (пользователь её не увидит):\n"
    "  [[ACTION:regenerate_workout|короткое пожелание]] — пересоздать тренировки;\n"
    "  [[ACTION:regenerate_nutrition|короткое пожелание]] — пересоздать питание;\n"
    "  [[ACTION:nutrition_from_food|продукты через запятую]] — составить рацион из этих продуктов.\n"
    "Если действие не нужно — не добавляй ACTION. В конце ВСЕГДА добавляй одну строку "
    "[[SUGGEST:вопрос1|вопрос2|вопрос3]] — 2–3 коротких уместных продолжения разговора."
)


async def chat(question: str, profile: dict | None = None, image: str | None = None) -> dict:
    """Ответ ИИ-тренера. Возвращает dict:
      {"answer": str, "actions": [{name, arg}], "suggestions": [str]}

    Если передано изображение — используется vision-модель. Явный офф-топик
    отсекается без обращения к модели.
    """
    # дешёвый фильтр: явный не-фитнес запрос — отказ без вызова API
    if not image and is_offtopic(question):
        return {"answer": _REFUSAL, "actions": [], "suggestions": []}

    system = _CHAT_SYSTEM
    ctx = _profile_context(profile)
    if ctx:
        system += f"\n\nДанные пользователя: {ctx}"

    if image:
        text = question or "Оцени, что на фото."
        # Свободная vision-модель часто отвечает текстом и забывает служебную
        # директиву. Явно напоминаем про неё для случая «фото еды → меняем питание».
        text += (
            "\n\n(Если на фото продукты или еда и пользователь просит составить/изменить "
            "питание — ОБЯЗАТЕЛЬНО добавь в конце служебную строку "
            "[[ACTION:nutrition_from_food|перечисли продукты с фото через запятую]].)"
        )
        user_content = [
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": image}},
        ]
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ]
        raw = await _chat(messages, model=settings.ai_vision_model)
    else:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": question},
        ]
        raw = await _chat(messages)

    answer, actions, suggestions = parse_directives(raw)
    if actions:
        logger.info("AI actions: %s", [a["name"] for a in actions])
    return {"answer": answer or raw, "actions": actions, "suggestions": suggestions}


# ============================================================
#  Генерация плана тренировок (структурированный JSON)
# ============================================================

# Части тела, под каждую — отдельная тренировка.
WORKOUT_GROUPS = ["Грудь", "Спина", "Ноги", "Руки"]


async def generate_workout_plan(profile: dict, extra: str | None = None) -> dict:
    """Сгенерировать структурированный план тренировок по профилю.

    extra — дополнительное пожелание пользователя (например, «замени приседания,
    болит колено»), добавляется к промпту.

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
        "Группы строго: Грудь, Спина, Ноги, Руки. 4–6 упражнений на группу. "
        "Поле reps — строка. rest — например «1 мин» или «90 сек»."
    )
    user = (
        f"Профиль: {ctx}\nУровень: {level}. Место: {place}.\n"
        f"Верни JSON по форме: {schema_hint}"
    )
    if extra:
        user += f"\nДополнительное пожелание пользователя (обязательно учти): {extra}"

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

async def generate_nutrition_plan(profile: dict, extra: str | None = None) -> dict:
    """Сгенерировать план питания на день под целевые калории/КБЖУ.

    extra — дополнительное пожелание/ограничение (например, список продуктов из
    холодильника или «без молочного»).

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
    if extra:
        user += f"\nОбязательно учти: {extra}"

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
