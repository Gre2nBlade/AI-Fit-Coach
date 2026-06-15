"""Сервис тренировок: генерация планов (через ai_service) и запись прогресса."""
from __future__ import annotations

from db.engine import async_session_factory
from db.repositories import user_repo, workout_repo
from services import ai_service


async def create_plan_for(tg_id: int) -> dict | None:
    """Сгенерировать план тренировок через AI и сохранить его."""
    async with async_session_factory() as session:
        user = await user_repo.get_by_tg_id(session, tg_id)
        if user is None:
            return None

        profile = {
            "sex": user.sex, "age": user.age,
            "height_cm": user.height_cm, "weight_kg": user.weight_kg,
        }
        ai_text = await ai_service.generate_workout(profile)

        plan = await workout_repo.create_plan(
            session, user_id=user.id, title="AI-план (черновик)", raw_ai_response=ai_text,
        )
        return {"id": plan.id, "title": plan.title, "raw_ai_response": plan.raw_ai_response}


async def list_plans(tg_id: int) -> list[dict]:
    async with async_session_factory() as session:
        user = await user_repo.get_by_tg_id(session, tg_id)
        if user is None:
            return []
        plans = await workout_repo.list_plans(session, user.id)
        return [{"id": p.id, "title": p.title, "created_at": str(p.created_at)} for p in plans]


async def log_result(tg_id: int, note: str) -> bool:
    async with async_session_factory() as session:
        user = await user_repo.get_by_tg_id(session, tg_id)
        if user is None:
            return False
        await workout_repo.log_workout(session, user.id, note=note)
        return True
