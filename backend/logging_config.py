"""Настройка логирования: консоль + файл с ротацией (stdlib).

Вызывается один раз на старте (backend/main.py и api/app.py).
"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from backend.config import settings

_configured = False


def setup_logging() -> None:
    global _configured
    if _configured:
        return

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    console = logging.StreamHandler()
    console.setFormatter(fmt)

    file_handler = RotatingFileHandler(
        log_dir / "app.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8",
    )
    file_handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(console)
    root.addHandler(file_handler)

    _configured = True
