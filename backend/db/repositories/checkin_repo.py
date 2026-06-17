"""Репозиторий ежедневных отметок (DailyCheckin). Только SQL по daily_checkins."""
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import DailyCheckin

# Поля-флаги, которые можно отмечать.
FLAGS = ("ate_well", "trained", "all_done")


async def get_day(session: AsyncSession, user_id: int, day: date) -> DailyCheckin | None:
    result = await session.execute(
        select(DailyCheckin).where(
            DailyCheckin.user_id == user_id, DailyCheckin.day == day
        )
    )
    return result.scalar_one_or_none()


async def upsert(session: AsyncSession, user_id: int, day: date, **flags) -> DailyCheckin:
    """Создать/обновить отметку дня. Принимает только поля из FLAGS (0/1)."""
    clean = {k: int(bool(v)) for k, v in flags.items() if k in FLAGS}
    row = await get_day(session, user_id, day)
    if row is None:
        row = DailyCheckin(user_id=user_id, day=day, **clean)
        session.add(row)
    else:
        for k, v in clean.items():
            setattr(row, k, v)
    await session.commit()
    await session.refresh(row)
    return row


async def list_range(
    session: AsyncSession, user_id: int, start: date, end: date
) -> list[DailyCheckin]:
    """Отметки за период [start, end] включительно, по возрастанию даты."""
    result = await session.execute(
        select(DailyCheckin)
        .where(
            DailyCheckin.user_id == user_id,
            DailyCheckin.day >= start,
            DailyCheckin.day <= end,
        )
        .order_by(DailyCheckin.day.asc())
    )
    return list(result.scalars().all())
