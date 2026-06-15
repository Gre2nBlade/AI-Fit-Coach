"""Точка входа: Telegram-бот + FastAPI в одном процессе через asyncio.gather().

Когда понадобится масштабирование — разносим на два контейнера без изменения кода.
"""
from __future__ import annotations

import asyncio
import logging

import uvicorn
from telegram.ext import Application

from api.app import app as fastapi_app
from bot.config import settings
from bot.handlers import nutrition, notifications, onboarding, progress, workout
from db.engine import init_db
from services import scheduler

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def build_bot() -> Application:
    """Собрать Telegram Application и зарегистрировать хендлеры."""
    application = Application.builder().token(settings.bot_token).build()

    onboarding.register(application)
    workout.register(application)
    nutrition.register(application)
    progress.register(application)
    notifications.register(application)

    return application


async def run_bot(application: Application) -> None:
    """Запустить polling вручную (без run_polling, чтобы делить event loop с uvicorn)."""
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    logger.info("Telegram-бот запущен (polling)")
    # Держим корутину живой
    await asyncio.Event().wait()


async def run_api() -> None:
    config = uvicorn.Config(
        fastapi_app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )
    server = uvicorn.Server(config)
    logger.info("FastAPI запускается на %s:%s", settings.api_host, settings.api_port)
    await server.serve()


async def main() -> None:
    await init_db()
    scheduler.start()

    application = build_bot()
    try:
        await asyncio.gather(run_bot(application), run_api())
    finally:
        scheduler.shutdown()
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
