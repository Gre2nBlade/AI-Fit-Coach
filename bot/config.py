"""Конфиг проекта. pydantic-settings читает .env и валидирует типы."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telegram
    bot_token: str = "PUT_TOKEN_HERE"

    # AI / OpenRouter
    openrouter_api_key: str = "PUT_KEY_HERE"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    ai_model: str = "anthropic/claude-3.5-sonnet"

    # БД
    database_url: str = "sqlite+aiosqlite:///./data/bot.db"

    # FastAPI
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    webapp_url: str = "https://example.com"

    # Прочее
    log_level: str = "INFO"
    cache_ttl: int = 300


settings = Settings()
