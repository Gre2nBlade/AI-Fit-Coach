"""Репозиторий пользователя. Единственное место с SQL по User/UserGoal/BodyMeasurement."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import BodyMeasurement, User, UserGoal


async def get_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def get_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create(session: AsyncSession, email: str, password_hash: str, **fields) -> User:
    user = User(email=email, password_hash=password_hash, **fields)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def update(session: AsyncSession, user: User, **fields) -> User:
    for key, value in fields.items():
        setattr(user, key, value)
    await session.commit()
    await session.refresh(user)
    return user


async def add_goal(session: AsyncSession, user_id: int, goal_type: str,
                   target_value: float | None = None) -> UserGoal:
    goal = UserGoal(user_id=user_id, goal_type=goal_type, target_value=target_value)
    session.add(goal)
    await session.commit()
    await session.refresh(goal)
    return goal


async def add_measurement(session: AsyncSession, user_id: int, **fields) -> BodyMeasurement:
    measurement = BodyMeasurement(user_id=user_id, **fields)
    session.add(measurement)
    await session.commit()
    await session.refresh(measurement)
    return measurement
