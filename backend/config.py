"""Конфиг бэкенда. pydantic-settings читает .env и валидирует типы."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # AI / OpenRouter
    openrouter_api_key: str = "PUT_KEY_HERE"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    # Основная модель — текстовые ответы, генерация планов.
    ai_model: str = "openai/gpt-oss-120b:free"
    # Vision-модель — анализ фото в чате (еда, упражнения). Поддерживает изображения.
    ai_vision_model: str = "google/gemma-4-26b-a4b-it:free"
    # Лимиты длины ответа — короче ответ = быстрее генерация.
    ai_max_tokens: int = 800          # чат ИИ-тренера
    ai_plan_max_tokens: int = 1500    # генерация планов (JSON)

    # БД
    database_url: str = "sqlite+aiosqlite:///./data/app.db"

    # JWT
    jwt_secret: str = "CHANGE_ME_IN_PROD"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # неделя

    # Admin — секрет для входа в админ-панель (email=admin, пароль=секрет).
    admin_secret: str = "CHANGE_ME_ADMIN_SECRET"

    # FastAPI
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    # CORS: домены фронта/мобилки. Для Capacitor — capacitor://localhost и т.п.
    cors_origins: list[str] = ["*"]

    # Прочее
    log_level: str = "INFO"
    cache_ttl: int = 300


settings = Settings()
