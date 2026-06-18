"""Сервис админ-панели: аналитика, управление пользователями и их контентом,
чтение логов. Не знает про HTTP. Доступ защищён секретом/админ-JWT (см. роутер).
"""
from __future__ import annotations

import json
import secrets
from collections import deque
from pathlib import Path

from backend.config import settings
from backend.db.engine import async_session_factory
from backend.db.repositories import admin_repo, user_repo
from backend.services import (
    auth_service,
    nutrition_service,
    user_service,
    workout_service,
)

_LOG_PATH = Path("logs") / "app.log"


def login(secret: str) -> dict | None:
    """Проверить секрет (compare_digest — защита от тайминг-атак).
    Вернуть {token} или None. Если секрет не настроен (плейсхолдер) — вход запрещён.
    """
    expected = settings.admin_secret or ""
    if not secret or expected.startswith("CHANGE_ME"):
        return None
    if secrets.compare_digest(secret, expected):
        return {"token": auth_service.create_admin_token()}
    return None


async def stats() -> dict:
    async with async_session_factory() as session:
        total = await admin_repo.count_users(session)
        onboarded = await admin_repo.count_onboarded(session)
        plans = await admin_repo.count_plans_by_kind(session)
        checkins = await admin_repo.count_checkins(session)
        active7 = await admin_repo.active_users(session, days=7)
        regs = await admin_repo.registrations_by_day(session, days=14)
    return {
        "users_total": total,
        "users_onboarded": onboarded,
        "active_users_7d": active7,
        "plans": plans,
        "checkins_total": checkins,
        "registrations_by_day": regs,
    }


async def users(q: str | None, limit: int, offset: int) -> dict:
    async with async_session_factory() as session:
        rows = await admin_repo.list_users(session, q=q, limit=limit, offset=offset)
        total = await admin_repo.count_users(session, q=q)
    items = [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "goal": u.goal,
            "level": u.level,
            "onboarded": bool(u.onboarded),
            "created_at": str(u.created_at),
        }
        for u in rows
    ]
    return {"items": items, "total": total, "limit": limit, "offset": offset}


async def user_detail(user_id: int) -> dict | None:
    profile = await user_service.get_profile(user_id)
    if profile is None:
        return None
    async with async_session_factory() as session:
        plans = await admin_repo.get_user_plans(session, user_id)
        checkins = await admin_repo.recent_checkins(session, user_id)
    profile["plans"] = [
        {"kind": p.kind, "updated_at": str(p.updated_at), "data": _safe_json(p.data_json)}
        for p in plans
    ]
    profile["checkins"] = [
        {
            "day": str(c.day),
            "ate_well": bool(c.ate_well),
            "trained": bool(c.trained),
            "all_done": bool(c.all_done),
        }
        for c in checkins
    ]
    return profile


async def update_user(user_id: int, fields: dict) -> dict | None:
    """Правка полей пользователя админом (валидация имени — как у пользователя)."""
    return await user_service.update_profile(user_id, **fields)


async def delete_user(user_id: int) -> bool:
    async with async_session_factory() as session:
        return await admin_repo.delete_user_cascade(session, user_id)


async def delete_plan(user_id: int, kind: str) -> bool:
    async with async_session_factory() as session:
        return await admin_repo.delete_plan(session, user_id, kind)


async def regenerate_plan(user_id: int, kind: str) -> dict | None:
    if kind == "workout":
        return await workout_service.regenerate(user_id)
    if kind == "nutrition":
        return await nutrition_service.regenerate(user_id)
    return None


async def user_exists(user_id: int) -> bool:
    async with async_session_factory() as session:
        return await user_repo.get_by_id(session, user_id) is not None


def read_logs(lines: int = 200) -> str:
    """Хвост файла логов (последние `lines` строк)."""
    if not _LOG_PATH.exists():
        return ""
    lines = max(1, min(lines, 2000))
    with _LOG_PATH.open("r", encoding="utf-8", errors="replace") as f:
        tail = deque(f, maxlen=lines)
    return "".join(tail)


def _safe_json(raw: str):
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
