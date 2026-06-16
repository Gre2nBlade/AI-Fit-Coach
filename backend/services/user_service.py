"""Сервис пользователя: профиль, цели, антропометрия.

Не знает ни про HTTP, ни про фреймворк. Работает по внутреннему user_id
(берётся из JWT). Сам управляет сессией БД.
"""
from __future__ import annotations

from backend.db.engine import async_session_factory
from backend.db.repositories import user_repo


async def get_profile(user_id: int) -> dict | None:
    async with async_session_factory() as session:
        user = await user_repo.get_by_id(session, user_id)
        return _to_dict(user) if user else None


async def update_profile(user_id: int, **fields) -> dict | None:
    # белый список полей, которые можно менять с фронта
    allowed = {"full_name", "sex", "age", "height_cm", "weight_kg"}
    fields = {k: v for k, v in fields.items() if k in allowed}
    async with async_session_factory() as session:
        user = await user_repo.get_by_id(session, user_id)
        if user is None:
            return None
        user = await user_repo.update(session, user, **fields)
        return _to_dict(user)


async def set_goal(user_id: int, goal_type: str, target_value: float | None = None) -> dict | None:
    async with async_session_factory() as session:
        user = await user_repo.get_by_id(session, user_id)
        if user is None:
            return None
        goal = await user_repo.add_goal(session, user.id, goal_type, target_value)
        return {"id": goal.id, "goal_type": goal.goal_type, "target_value": goal.target_value}


def _to_dict(user) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "sex": user.sex,
        "age": user.age,
        "height_cm": user.height_cm,
        "weight_kg": user.weight_kg,
    }
