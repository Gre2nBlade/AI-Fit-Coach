"""Репозиторий кэша ИИ-планов (AiPlan). Только SQL по таблице ai_plans."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import AiPlan


async def get(session: AsyncSession, user_id: int, kind: str) -> AiPlan | None:
    result = await session.execute(
        select(AiPlan).where(AiPlan.user_id == user_id, AiPlan.kind == kind)
    )
    return result.scalar_one_or_none()


async def upsert(session: AsyncSession, user_id: int, kind: str, data_json: str) -> AiPlan:
    """Создать или обновить план данного вида для пользователя."""
    plan = await get(session, user_id, kind)
    if plan is None:
        plan = AiPlan(user_id=user_id, kind=kind, data_json=data_json)
        session.add(plan)
    else:
        plan.data_json = data_json
    await session.commit()
    await session.refresh(plan)
    return plan
