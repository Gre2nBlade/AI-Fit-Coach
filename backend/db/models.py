"""ORM-модели. Черновой набор. Аутентификация — email + пароль (хеш)."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sex: Mapped[str | None] = mapped_column(String(8), nullable=True)        # male/female
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    goal_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    goal: Mapped[str | None] = mapped_column(String(32), nullable=True)       # Похудение/Набор массы/Баланс формы
    level: Mapped[str | None] = mapped_column(String(32), nullable=True)      # Начальный/Средний/Продвинутый
    place: Mapped[str | None] = mapped_column(String(32), nullable=True)      # Дома/В зале/На улице
    training_days: Mapped[str | None] = mapped_column(String(64), nullable=True)  # "ПН,СР,ПТ"
    avatar: Mapped[str | None] = mapped_column(String, nullable=True)         # data URL (base64), черновик
    onboarded: Mapped[int] = mapped_column(Integer, default=0)               # 0/1 — пройден ли онбординг
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    goals: Mapped[list["UserGoal"]] = relationship(back_populates="user")
    measurements: Mapped[list["BodyMeasurement"]] = relationship(back_populates="user")
    workout_plans: Mapped[list["WorkoutPlan"]] = relationship(back_populates="user")


class UserGoal(Base):
    __tablename__ = "user_goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    goal_type: Mapped[str] = mapped_column(String(32))      # lose_weight / gain_muscle / ...
    target_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="goals")


class BodyMeasurement(Base):
    __tablename__ = "body_measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    waist_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    measured_at: Mapped[date] = mapped_column(Date, server_default=func.current_date())

    user: Mapped["User"] = relationship(back_populates="measurements")


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(128))
    raw_ai_response: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="workout_plans")
    exercises: Mapped[list["Exercise"]] = relationship(back_populates="plan")


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("workout_plans.id"))
    name: Mapped[str] = mapped_column(String(128))
    sets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reps: Mapped[int | None] = mapped_column(Integer, nullable=True)

    plan: Mapped["WorkoutPlan"] = relationship(back_populates="exercises")


class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    exercise_id: Mapped[int | None] = mapped_column(ForeignKey("exercises.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    logged_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class FoodEntry(Base):
    __tablename__ = "food_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(128))
    calories: Mapped[float | None] = mapped_column(Float, nullable=True)
    protein: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs: Mapped[float | None] = mapped_column(Float, nullable=True)
    eaten_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DailyNutrition(Base):
    __tablename__ = "daily_nutrition"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    day: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    total_calories: Mapped[float] = mapped_column(Float, default=0.0)
    total_protein: Mapped[float] = mapped_column(Float, default=0.0)
    total_fat: Mapped[float] = mapped_column(Float, default=0.0)
    total_carbs: Mapped[float] = mapped_column(Float, default=0.0)


class AiPlan(Base):
    """Кэш сгенерированного ИИ плана (тренировки/питание) в виде JSON-строки.

    На пользователя — по одной актуальной записи каждого вида (kind).
    Перегенерация заменяет data_json существующей записи.
    """

    __tablename__ = "ai_plans"
    __table_args__ = (UniqueConstraint("user_id", "kind", name="uq_aiplan_user_kind"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(16))            # workout | nutrition
    data_json: Mapped[str] = mapped_column(Text)             # структура плана (JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class DailyCheckin(Base):
    """Ежедневная отметка пользователя: питание/тренировка/всё выполнено.

    Источник реального прогресса. Уникальна по (user_id, day) — одна запись на день.
    Флаги хранятся как 0/1 (Integer) — единообразно с User.onboarded.
    """

    __tablename__ = "daily_checkins"
    __table_args__ = (UniqueConstraint("user_id", "day", name="uq_checkin_user_day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    ate_well: Mapped[int] = mapped_column(Integer, default=0)     # питался правильно
    trained: Mapped[int] = mapped_column(Integer, default=0)      # тренировался
    all_done: Mapped[int] = mapped_column(Integer, default=0)     # выполнил всё
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
