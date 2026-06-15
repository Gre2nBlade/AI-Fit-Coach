"""APScheduler 3.x — напоминания и фоновые задачи.

Черновик: один планировщик на процесс, задачи регистрируются на старте.
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _daily_reminder() -> None:
    # TODO: рассылка напоминаний пользователям
    logger.info("Scheduler tick: daily_reminder (черновик)")


def setup_jobs() -> None:
    """Зарегистрировать задачи. Вызывается из bot.main перед стартом."""
    scheduler.add_job(_daily_reminder, "interval", hours=24, id="daily_reminder")


def start() -> None:
    setup_jobs()
    scheduler.start()
    logger.info("APScheduler запущен")


def shutdown() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
