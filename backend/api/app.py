"""FastAPI-приложение. Отдаёт JSON-роутеры для веб-/мобильного клиента.

Статику фронта в проде отдаёт отдельный веб-сервер (или она внутри APK через
Capacitor). Здесь — только API.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routers import ai, auth, nutrition, user, workout
from backend.config import settings
from backend.db.engine import init_db
from backend.logging_config import setup_logging
from backend.services import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await init_db()
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="AI Fit Coach API", version="0.0.1-draft", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(workout.router)
app.include_router(nutrition.router)
app.include_router(ai.router)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Понятное сообщение об ошибке ввода вместо технического дампа pydantic."""
    msg = "Проверьте введённые данные."
    for err in exc.errors():
        field = err.get("loc", ["", ""])[-1]
        etype = err.get("type", "")
        if field == "password" and etype == "string_too_short":
            limit = err.get("ctx", {}).get("min_length", 6)
            msg = f"Пароль слишком короткий: минимум {limit} символов."
            break
        if field == "email":
            msg = "Некорректный email."
            break
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": msg})


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
