"""/start и онбординг нового пользователя.

Черновик: без FSM-сбора данных, просто регистрируем юзера и показываем кнопки.
Тут только Telegram-логика — вся бизнес-логика в services/.
"""
from __future__ import annotations

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    WebAppInfo,
)
from telegram.ext import Application, CommandHandler, ContextTypes

from bot.config import settings
from services import user_service


def _main_menu() -> InlineKeyboardMarkup:
    # Голые кнопки без дизайна — основное меню.
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🏋️ Тренировка", callback_data="menu:workout")],
            [InlineKeyboardButton("🍎 Питание", callback_data="menu:nutrition")],
            [InlineKeyboardButton("📊 Прогресс", callback_data="menu:progress")],
            [InlineKeyboardButton("⏰ Напоминания", callback_data="menu:notifications")],
            [InlineKeyboardButton("📱 Открыть MiniApp", web_app=WebAppInfo(url=settings.webapp_url))],
        ]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    await user_service.get_or_create(
        tg_id=tg_user.id,
        username=tg_user.username,
        full_name=tg_user.full_name,
    )
    await update.message.reply_text(
        "Привет! Это AI Fit Coach (черновик).\nВыбери раздел:",
        reply_markup=_main_menu(),
    )


def register(app: Application) -> None:
    app.add_handler(CommandHandler("start", start))
