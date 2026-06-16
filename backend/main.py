"""Точка входа бэкенда: FastAPI через uvicorn + старт планировщика и БД."""
from __future__ import annotations

import uvicorn

from backend.config import settings
from backend.logging_config import setup_logging

setup_logging()


def main() -> None:
    uvicorn.run(
        "backend.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
