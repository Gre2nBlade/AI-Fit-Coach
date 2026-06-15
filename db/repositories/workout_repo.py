"""Репозиторий тренировок: WorkoutPlan, Exercise, WorkoutLog. Только SQL."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Exercise, WorkoutLog, WorkoutPlan


async def create_plan(session: AsyncSession, user_id: int, title: str,
                      raw_ai_response: str | None = None) -> WorkoutPlan:
    plan = WorkoutPlan(user_id=user_id, title=title, raw_ai_response=raw_ai_response)
    session.add(plan)
    await session.commit()
    await session.refresh(plan)
    return plan


async def add_exercise(session: AsyncSession, plan_id: int, name: str,
                       sets: int | None = None, reps: int | None = None) -> Exercise:
    exercise = Exercise(plan_id=plan_id, name=name, sets=sets, reps=reps)
    session.add(exercise)
    await session.commit()
    await session.refresh(exercise)
    return exercise


async def list_plans(session: AsyncSession, user_id: int) -> list[WorkoutPlan]:
    result = await session.execute(
        select(WorkoutPlan).where(WorkoutPlan.user_id == user_id)
        .order_by(WorkoutPlan.created_at.desc())
    )
    return list(result.scalars().all())


async def log_workout(session: AsyncSession, user_id: int,
                      exercise_id: int | None = None, note: str | None = None) -> WorkoutLog:
    log = WorkoutLog(user_id=user_id, exercise_id=exercise_id, note=note)
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log
