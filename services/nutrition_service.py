"""Сервис питания: расчёт КБЖУ и ведение дневника."""
from __future__ import annotations

from db.engine import async_session_factory
from db.repositories import nutrition_repo, user_repo


async def add_food(tg_id: int, name: str, calories: float | None = None,
                   protein: float | None = None, fat: float | None = None,
                   carbs: float | None = None) -> dict | None:
    async with async_session_factory() as session:
        user = await user_repo.get_by_tg_id(session, tg_id)
        if user is None:
            return None
        entry = await nutrition_repo.add_food_entry(
            session, user.id, name=name,
            calories=calories, protein=protein, fat=fat, carbs=carbs,
        )
        return {"id": entry.id, "name": entry.name, "calories": entry.calories}


async def get_diary(tg_id: int) -> list[dict]:
    async with async_session_factory() as session:
        user = await user_repo.get_by_tg_id(session, tg_id)
        if user is None:
            return []
        entries = await nutrition_repo.list_entries(session, user.id)
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
