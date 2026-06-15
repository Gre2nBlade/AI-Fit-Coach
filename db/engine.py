"""Async-движок и фабрика сессий SQLAlchemy.

Переезд на PostgreSQL = поменять только DATABASE_URL в .env, например:
    postgresql+asyncpg://user:pass@localhost/fitcoach
Весь остальной код (модели, репозитории, сервисы) не трогается.
"""
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bot.config import settings
from db.base import Base

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
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Выдать новую сессию. Используется как async context manager."""
    return async_session_factory()
