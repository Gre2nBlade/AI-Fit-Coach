"""Простой in-memory кэш: dict + TTL.

Интерфейс (get / set / delete) совместим с будущим RedisCache —
когда понадобится Redis, создаётся redis_cache.py с теми же методами,
и меняется одна строка импорта.

ВНИМАНИЕ (черновик): TTL проверяется лениво при чтении, без фоновой чистки.
"""
from __future__ import annotations

import time
from typing import Any


class MemoryCache:
    def __init__(self, default_ttl: int = 300) -> None:
        self._default_ttl = default_ttl
        self._store: dict[str, tuple[Any, float | None]] = {}

    def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if item is None:
            return None
        value, expires_at = item
        if expires_at is not None and time.monotonic() > expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        ttl = self._default_ttl if ttl is None else ttl
        expires_at = time.monotonic() + ttl if ttl > 0 else None
        self._store[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()


# Глобальный инстанс — импортируется сервисами.
cache = MemoryCache()
