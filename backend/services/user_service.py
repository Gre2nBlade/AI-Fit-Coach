"""Сервис пользователя: профиль, цели, антропометрия + производные расчёты.

Не знает ни про HTTP, ни про фреймворк. Работает по внутреннему user_id
(берётся из JWT). Сам управляет сессией БД.
"""
from __future__ import annotations

from backend.db.engine import async_session_factory
from backend.db.repositories import user_repo

# Поля, которые фронт может менять (онбординг + профиль).
EDITABLE_FIELDS = {
    "full_name", "sex", "age", "height_cm", "weight_kg",
    "goal_weight_kg", "goal", "level", "place", "training_days", "avatar",
}


async def get_profile(user_id: int) -> dict | None:
    async with async_session_factory() as session:
        user = await user_repo.get_by_id(session, user_id)
        return _to_dict(user) if user else None


async def update_profile(user_id: int, **fields) -> dict | None:
    fields = {k: v for k, v in fields.items() if k in EDITABLE_FIELDS}
    # Имя задаётся пользователем — валидируем на сервере (на случай обхода клиента).
    if "full_name" in fields and fields["full_name"] is not None:
        if len((fields["full_name"] or "").strip()) < 2:
            raise ValueError("Имя должно быть не короче 2 символов.")
    async with async_session_factory() as session:
        user = await user_repo.get_by_id(session, user_id)
        if user is None:
            return None
        # если пришли базовые данные — считаем онбординг пройденным
        if fields.get("goal") and fields.get("age") and fields.get("weight_kg"):
            fields["onboarded"] = 1
        user = await user_repo.update(session, user, **fields)
        return _to_dict(user)


def _to_dict(user) -> dict:
    data = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "sex": user.sex,
        "age": user.age,
        "height_cm": user.height_cm,
        "weight_kg": user.weight_kg,
        "goal_weight_kg": user.goal_weight_kg,
        "goal": user.goal,
        "level": user.level,
        "place": user.place,
        "training_days": user.training_days,
        "avatar": user.avatar,
        "onboarded": bool(user.onboarded),
    }
    data["metrics"] = compute_metrics(user)
    return data


# ---------- Производные метрики (BMR / TDEE / BMI / КБЖУ) ----------

_ACTIVITY = {0: 1.2, 1: 1.3, 2: 1.4, 3: 1.5, 4: 1.6, 5: 1.7, 6: 1.8, 7: 1.9}


def compute_metrics(user) -> dict | None:
    """Посчитать калории/КБЖУ/BMI из профиля. None, если данных не хватает."""
    if not (user.age and user.height_cm and user.weight_kg and user.sex):
        return None

    weight = float(user.weight_kg)
    height = float(user.height_cm)
    age = int(user.age)
    is_male = str(user.sex).lower().startswith(("м", "m"))

    # BMR (Миффлин — Сан Жеор)
    bmr = 10 * weight + 6.25 * height - 5 * age + (5 if is_male else -161)

    # число тренировочных дней → коэффициент активности
    days = len([d for d in (user.training_days or "").split(",") if d.strip()])
    tdee = bmr * _ACTIVITY.get(days, 1.4)

    # коррекция под цель
    goal = (user.goal or "").lower()
    if "похуд" in goal:
        calories = tdee - 400
    elif "набор" in goal or "масс" in goal:
        calories = tdee + 350
    else:
        calories = tdee

    calories = round(calories)

    # КБЖУ: белок 2 г/кг, жиры 1 г/кг, остальное — углеводы
    protein_g = round(weight * 2)
    fat_g = round(weight * 1)
    carbs_g = max(0, round((calories - protein_g * 4 - fat_g * 9) / 4))

    bmi = round(weight / ((height / 100) ** 2), 1)
    water_l = round(weight * 0.033, 1)

    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "calories": calories,
        "protein_g": protein_g,
        "fat_g": fat_g,
        "carbs_g": carbs_g,
        "bmi": bmi,
        "water_l": water_l,
        "training_days_count": days,
    }
