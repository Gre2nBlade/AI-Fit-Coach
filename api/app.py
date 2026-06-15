"""FastAPI-приложение для MiniApp.

Отдаёт JSON роутерам + статику miniapp/. Запускается из bot.main через uvicorn.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routers import nutrition, user, workout

app = FastAPI(title="AI Fit Coach API", version="0.0.1-draft")

# Черновик: разрешаем всё. В проде — сузить до домена MiniApp.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(workout.router)
app.include_router(nutrition.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


# Статика MiniApp — отдаётся FastAPI напрямую (в проде можно через nginx).
_miniapp_dir = Path(__file__).resolve().parent.parent / "miniapp"
if _miniapp_dir.exists():
    app.mount("/app", StaticFiles(directory=str(_miniapp_dir), html=True), name="miniapp")
