"""Репозиторий питания: FoodEntry, DailyNutrition. Только SQL."""
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import DailyNutrition, FoodEntry


async def add_food_entry(session: AsyncSession, user_id: int, name: str,
                         calories: float | None = None, protein: float | None = None,
                         fat: float | None = None, carbs: float | None = None) -> FoodEntry:
    entry = FoodEntry(
        user_id=user_id, name=name,
        calories=calories, protein=protein, fat=fat, carbs=carbs,
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


async def list_entries(session: AsyncSession, user_id: int) -> list[FoodEntry]:
    result = await session.execute(
        select(FoodEntry).where(FoodEntry.user_id == user_id)
        .order_by(FoodEntry.eaten_at.desc())
    )
    return list(result.scalars().all())


async def get_daily(session: AsyncSession, user_id: int, day: date | None = None) -> DailyNutrition | None:
    stmt = select(DailyNutrition).where(DailyNutrition.user_id == user_id)
    if day is not None:
        stmt = stmt.where(DailyNutrition.day == day)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
