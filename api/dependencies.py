"""Аутентификация MiniApp.

Telegram при открытии WebApp передаёт initData — строку с данными пользователя
и HMAC-SHA256 подписью. Здесь подпись проверяется. Без этой проверки API открыт
для любых запросов.

Алгоритм (по докам Telegram):
  secret_key = HMAC_SHA256(key="WebAppData", msg=BOT_TOKEN)
  hash       = HMAC_SHA256(key=secret_key, msg=data_check_string)
  data_check_string — все поля initData (кроме hash), отсортированные по ключу,
  склеенные как "k=v" через \\n.

get_current_user используется как Depends во всех роутерах.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException, status

from bot.config import settings


def _verify_init_data(init_data: str) -> dict:
    """Проверить подпись initData и вернуть распарсенные поля."""
    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="bad initData")

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="no hash")

    data_check_string = "\n".join(f"{k}={parsed[k]}" for k in sorted(parsed))

    secret_key = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calc_hash, received_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="bad signature")

    return parsed


async def get_current_user(
    x_telegram_init_data: str = Header(default="", alias="X-Telegram-Init-Data"),
) -> dict:
    """FastAPI-зависимость: вернуть профиль Telegram-пользователя из initData.

    Возвращает dict с как минимум tg_id (id из user). Используется через Depends.
    """
    if not x_telegram_init_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing init data")

    parsed = _verify_init_data(x_telegram_init_data)

    user_json = parsed.get("user")
    if not user_json:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="no user")

    try:
        user = json.loads(user_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="bad user json")

    return {
        "tg_id": user.get("id"),
        "username": user.get("username"),
        "full_name": " ".join(filter(None, [user.get("first_name"), user.get("last_name")])) or None,
    }
