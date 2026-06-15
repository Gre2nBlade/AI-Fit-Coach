"""Сервис пользователя: профиль, цели, антропометрия.

Не знает ни про Telegram, ни про HTTP. Вызывается и хендлерами, и роутерами.
Работает через репозиторий, сам управляет сессией БД.
"""
from __future__ import annotations

from db.engine import async_session_factory
from db.repositories import user_repo


async def get_or_create(tg_id: int, username: str | None = None,
                        full_name: str | None = None) -> dict:
    """Найти пользователя по tg_id или создать нового. Возвращает dict-профиль."""
    async with async_session_factory() as session:
        user = await user_repo.get_by_tg_id(session, tg_id)
        if user is None:
            user = await user_repo.create(
                session, tg_id=tg_id, username=username, full_name=full_name,
            )
        return _to_dict(user)


async def get_profile(tg_id: int) -> dict | None:
    async with async_session_factory() as session:
        user = await user_repo.get_by_tg_id(session, tg_id)
        return _to_dict(user) if user else None


async def update_profile(tg_id: int, **fields) -> dict | None:
    async with async_session_factory() as session:
        user = await user_repo.get_by_tg_id(session, tg_id)
        if user is None:
            return None
        user = await user_repo.update(session, user, **fields)
        return _to_dict(user)


async def set_goal(tg_id: int, goal_type: str, target_value: float | None = None) -> dict | None:
    async with async_session_factory() as session:
        user = await user_repo.get_by_tg_id(session, tg_id)
        if user is None:
            return None
        goal = await user_repo.add_goal(session, user.id, goal_type, target_value)
        return {"id": goal.id, "goal_type": goal.goal_type, "target_value": goal.target_value}


def _to_dict(user) -> dict:
    return {
        "id": user.id,
        "tg_id": user.tg_id,
        "username": user.username,
        "full_name": user.full_name,
        "sex": user.sex,
        "age": user.age,
        "height_cm": user.height_cm,
        "weight_kg": user.weight_kg,
    }
