"""Сервис питания: расчёт КБЖУ и ведение дневника."""
from __future__ import annotations

from backend.db.engine import async_session_factory
from backend.db.repositories import nutrition_repo


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
