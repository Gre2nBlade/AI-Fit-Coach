"""Сервис питания: расчёт КБЖУ, ИИ-план питания и ведение дневника."""
from __future__ import annotations

import json

from backend.db.engine import async_session_factory
from backend.db.repositories import ai_plan_repo, nutrition_repo
from backend.services import ai_service, user_service

_KIND = "nutrition"


async def get_plan(user_id: int, force: bool = False) -> dict | None:
    """Вернуть кэшированный план питания; при отсутствии (или force) — сгенерировать."""
    profile = await user_service.get_profile(user_id)
    if profile is None:
        return None

    if not force:
        async with async_session_factory() as session:
            cached = await ai_plan_repo.get(session, user_id, _KIND)
            if cached is not None:
                try:
                    return json.loads(cached.data_json)
                except (json.JSONDecodeError, TypeError):
                    pass

    plan = await ai_service.generate_nutrition_plan(profile)
    async with async_session_factory() as session:
        await ai_plan_repo.upsert(session, user_id, _KIND, json.dumps(plan, ensure_ascii=False))
    return plan


async def regenerate(user_id: int, extra: str | None = None) -> dict | None:
    """Пересоздать план питания (с опциональным пожеланием) и сохранить."""
    profile = await user_service.get_profile(user_id)
    if profile is None:
        return None
    plan = await ai_service.generate_nutrition_plan(profile, extra=extra)
    async with async_session_factory() as session:
        await ai_plan_repo.upsert(session, user_id, _KIND, json.dumps(plan, ensure_ascii=False))
    return plan


async def add_food(user_id: int, name: str, calories: float | None = None,
                   protein: float | None = None, fat: float | None = None,
                   carbs: float | None = None) -> dict:
    async with async_session_factory() as session:
        entry = await nutrition_repo.add_food_entry(
            session, user_id, name=name,
            calories=calories, protein=protein, fat=fat, carbs=carbs,
        )
        return {"id": entry.id, "name": entry.name, "calories": entry.calories}


async def get_diary(user_id: int) -> list[dict]:
    async with async_session_factory() as session:
        entries = await nutrition_repo.list_entries(session, user_id)
        return [
            {
                "id": e.id, "name": e.name, "calories": e.calories,
                "protein": e.protein, "fat": e.fat, "carbs": e.carbs,
                "eaten_at": str(e.eaten_at),
            }
            for e in entries
        ]


def calc_bmr(sex: str, weight_kg: float, height_cm: float, age: int) -> float:
    """Базовый обмен веществ (Миффлин — Сан Жеор). Черновая формула."""
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + (5 if sex == "male" else -161)
