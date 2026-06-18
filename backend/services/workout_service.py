"""Сервис тренировок: генерация структурированных планов (через ai_service),
кэширование в AiPlan и запись прогресса."""
from __future__ import annotations

import json

from datetime import date

from backend.db.engine import async_session_factory
from backend.db.repositories import ai_plan_repo, checkin_repo, workout_repo
from backend.services import ai_service, user_service

_KIND = "workout"


async def get_plan(user_id: int, force: bool = False) -> dict | None:
    """Вернуть кэшированный план тренировок; при отсутствии (или force) — сгенерировать."""
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
                    pass  # битый кэш — перегенерируем

    plan = await ai_service.generate_workout_plan(profile)
    async with async_session_factory() as session:
        await ai_plan_repo.upsert(session, user_id, _KIND, json.dumps(plan, ensure_ascii=False))
    return plan


async def regenerate(user_id: int, extra: str | None = None) -> dict | None:
    """Пересоздать план тренировок (с опциональным пожеланием) и сохранить."""
    profile = await user_service.get_profile(user_id)
    if profile is None:
        return None
    plan = await ai_service.generate_workout_plan(profile, extra=extra)
    async with async_session_factory() as session:
        await ai_plan_repo.upsert(session, user_id, _KIND, json.dumps(plan, ensure_ascii=False))
    return plan


async def list_plans(user_id: int) -> list[dict]:
    async with async_session_factory() as session:
        plans = await workout_repo.list_plans(session, user_id)
        return [{"id": p.id, "title": p.title, "created_at": str(p.created_at)} for p in plans]


async def log_result(user_id: int, note: str) -> bool:
    async with async_session_factory() as session:
        await workout_repo.log_workout(session, user_id, note=note)
        return True


async def complete(user_id: int, note: str | None = None) -> dict:
    """Засчитать завершённую тренировку: записать лог и отметить день как
    тренировочный (trained=True). Возвращает обновлённую отметку дня."""
    today = date.today()
    async with async_session_factory() as session:
        await workout_repo.log_workout(session, user_id, note=note or "Тренировка завершена")
        row = await checkin_repo.upsert(session, user_id, today, trained=True)
    return {
        "day": str(row.day),
        "ate_well": bool(row.ate_well),
        "trained": bool(row.trained),
        "all_done": bool(row.all_done),
    }
