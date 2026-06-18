"""Репозиторий админ-панели. Единственное место с SQL для админ-операций:
списки/счётчики пользователей, аналитика, каскадное удаление, управление планами.
"""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import (
    AiPlan,
    BodyMeasurement,
    DailyCheckin,
    DailyNutrition,
    Exercise,
    FoodEntry,
    User,
    UserGoal,
    WorkoutLog,
    WorkoutPlan,
)


async def list_users(
    session: AsyncSession, q: str | None = None, limit: int = 50, offset: int = 0
) -> list[User]:
    stmt = select(User).order_by(User.created_at.desc())
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(User.email.ilike(like), User.full_name.ilike(like)))
    stmt = stmt.limit(limit).offset(offset)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def count_users(session: AsyncSession, q: str | None = None) -> int:
    stmt = select(func.count(User.id))
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(User.email.ilike(like), User.full_name.ilike(like)))
    return int((await session.execute(stmt)).scalar() or 0)


async def count_onboarded(session: AsyncSession) -> int:
    stmt = select(func.count(User.id)).where(User.onboarded == 1)
    return int((await session.execute(stmt)).scalar() or 0)


async def count_plans_by_kind(session: AsyncSession) -> dict[str, int]:
    stmt = select(AiPlan.kind, func.count(AiPlan.id)).group_by(AiPlan.kind)
    rows = (await session.execute(stmt)).all()
    return {kind: int(cnt) for kind, cnt in rows}


async def count_checkins(session: AsyncSession) -> int:
    stmt = select(func.count(DailyCheckin.id))
    return int((await session.execute(stmt)).scalar() or 0)


async def active_users(session: AsyncSession, days: int = 7) -> int:
    """Уникальные пользователи с чек-ином за последние `days` дней."""
    since = date.today() - timedelta(days=days)
    stmt = select(func.count(func.distinct(DailyCheckin.user_id))).where(
        DailyCheckin.day >= since
    )
    return int((await session.execute(stmt)).scalar() or 0)


async def registrations_by_day(session: AsyncSession, days: int = 14) -> list[dict]:
    """Число регистраций по дням за последние `days` дней (по возрастанию даты)."""
    since = date.today() - timedelta(days=days - 1)
    day_col = func.date(User.created_at)
    stmt = (
        select(day_col.label("day"), func.count(User.id).label("cnt"))
        .where(func.date(User.created_at) >= since.isoformat())
        .group_by(day_col)
        .order_by(day_col)
    )
    rows = (await session.execute(stmt)).all()
    return [{"day": str(day), "count": int(cnt)} for day, cnt in rows]


async def get_user_plans(session: AsyncSession, user_id: int) -> list[AiPlan]:
    stmt = select(AiPlan).where(AiPlan.user_id == user_id).order_by(AiPlan.kind)
    return list((await session.execute(stmt)).scalars().all())


async def recent_checkins(session: AsyncSession, user_id: int, limit: int = 14) -> list[DailyCheckin]:
    stmt = (
        select(DailyCheckin)
        .where(DailyCheckin.user_id == user_id)
        .order_by(DailyCheckin.day.desc())
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().all())


async def delete_plan(session: AsyncSession, user_id: int, kind: str) -> bool:
    result = await session.execute(
        delete(AiPlan).where(AiPlan.user_id == user_id, AiPlan.kind == kind)
    )
    await session.commit()
    return (result.rowcount or 0) > 0


async def delete_user_cascade(session: AsyncSession, user_id: int) -> bool:
    """Удалить пользователя и все связанные строки (FK без ON DELETE CASCADE —
    чистим вручную: сначала дети, затем сам User)."""
    user = await session.get(User, user_id)
    if user is None:
        return False

    # упражнения принадлежат планам тренировок пользователя
    plan_ids = (
        await session.execute(select(WorkoutPlan.id).where(WorkoutPlan.user_id == user_id))
    ).scalars().all()
    if plan_ids:
        await session.execute(delete(Exercise).where(Exercise.plan_id.in_(plan_ids)))

    for model in (
        AiPlan, DailyCheckin, WorkoutLog, FoodEntry,
        DailyNutrition, BodyMeasurement, UserGoal, WorkoutPlan,
    ):
        await session.execute(delete(model).where(model.user_id == user_id))

    await session.execute(delete(User).where(User.id == user_id))
    await session.commit()
    return True
