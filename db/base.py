"""Базовый класс для всех ORM-моделей (SQLAlchemy 2.0 DeclarativeBase)."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Все модели наследуются от этого класса."""
    pass
