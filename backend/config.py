"""Конфиг бэкенда. pydantic-settings читает .env и валидирует типы."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # AI / OpenRouter
    openrouter_api_key: str = "PUT_KEY_HERE"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    ai_model: str = "anthropic/claude-3.5-sonnet"

    # БД
    database_url: str = "sqlite+aiosqlite:///./data/app.db"

    # JWT
    jwt_secret: str = "CHANGE_ME_IN_PROD"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # неделя

    # FastAPI
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    # CORS: домены фронта/мобилки. Для Capacitor — capacitor://localhost и т.п.
    cors_origins: list[str] = ["*"]

    # Прочее
    log_level: str = "INFO"
    cache_ttl: int = 300


settings = Settings()
