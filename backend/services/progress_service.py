"""Сервис прогресса: ежедневные отметки (чек-ин) и агрегаты для графиков.

Реальный прогресс считается из таблицы daily_checkins (3 флага в день):
ate_well (питался правильно), trained (тренировался), all_done (выполнил всё).
"""
from __future__ import annotations

from datetime import date, timedelta

from backend.db.engine import async_session_factory
from backend.db.repositories import checkin_repo

_WEEK_LABELS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def _row_to_dict(row) -> dict:
    return {
        "day": str(row.day),
        "ate_well": bool(row.ate_well),
        "trained": bool(row.trained),
        "all_done": bool(row.all_done),
    }


async def get_today(user_id: int, today: date | None = None) -> dict:
    """Отметка за сегодня (если нет — все флаги false)."""
    today = today or date.today()
    async with async_session_factory() as session:
        row = await checkin_repo.get_day(session, user_id, today)
    if row is None:
        return {"day": str(today), "ate_well": False, "trained": False, "all_done": False}
    return _row_to_dict(row)


async def set_checkin(user_id: int, ate_well: bool, trained: bool, all_done: bool,
                      today: date | None = None) -> dict:
    """Сохранить отметку за сегодня."""
    today = today or date.today()
    async with async_session_factory() as session:
        row = await checkin_repo.upsert(
            session, user_id, today,
            ate_well=ate_well, trained=trained, all_done=all_done,
        )
    return _row_to_dict(row)


async def get_summary(user_id: int, today: date | None = None) -> dict:
    """Агрегаты для вкладки «Прогресс».

    - week_bars: тренировки по дням текущей недели (Пн..Вс) для столбиков;
    - workouts_month: число тренировок в текущем месяце;
    - completion_pct: % дней месяца с реальной тренировкой;
    - streak: текущая серия подряд дней с тренировкой (до сегодня).
    """
    today = today or date.today()
    monday = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    start = min(monday, month_start)

    async with async_session_factory() as session:
        rows = await checkin_repo.list_range(session, user_id, start, today)
    by_day = {r.day: r for r in rows}

    # столбики по дням текущей недели
    week_bars = []
    for i, label in enumerate(_WEEK_LABELS):
        d = monday + timedelta(days=i)
        r = by_day.get(d)
        week_bars.append({
            "label": label,
            "trained": bool(r and r.trained),
            "future": d > today,
        })

    # статистика месяца
    workouts_month = sum(
        1 for d, r in by_day.items() if d >= month_start and r.trained
    )
    days_passed = today.day  # сколько дней месяца прошло (включая сегодня)
    # «Выполнение плана» = доля дней месяца с реальной тренировкой.
    completion_pct = round(workouts_month / days_passed * 100) if days_passed else 0

    # серия подряд тренировок (от сегодня назад)
    streak = 0
    d = today
    while True:
        r = by_day.get(d)
        if r and r.trained:
            streak += 1
            d -= timedelta(days=1)
        else:
            break

    return {
        "week_bars": week_bars,
        "workouts_month": workouts_month,
        "completion_pct": completion_pct,
        "streak": streak,
        "today": await get_today(user_id, today),
    }
