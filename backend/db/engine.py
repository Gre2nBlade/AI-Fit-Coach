"""Async-движок и фабрика сессий SQLAlchemy.

Переезд на PostgreSQL = поменять только DATABASE_URL в .env, например:
    postgresql+asyncpg://user:pass@localhost/fitcoach
Весь остальной код (модели, репозитории, сервисы) не трогается.
"""
import os

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.config import settings
from backend.db.base import Base


def _ensure_sqlite_dir(database_url: str) -> None:
    """Создать каталог под sqlite-файл, иначе 'unable to open database file'."""
    url = make_url(database_url)
    if url.drivername.startswith("sqlite") and url.database and url.database != ":memory:":
        directory = os.path.dirname(url.database)
        if directory:
            os.makedirs(directory, exist_ok=True)


_ensure_sqlite_dir(settings.database_url)

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
)

# expire_on_commit=False — чтобы объекты оставались живыми после commit
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Создать таблицы (черновой вариант вместо Alembic)."""
    # импорт моделей, чтобы они зарегистрировались в metadata
    from backend.db import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
