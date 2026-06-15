"""/progress — статистика и графики. Черновик: заглушка с кнопкой в MiniApp."""
from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

from bot.config import settings


async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("📈 Открыть дашборд", web_app=WebAppInfo(url=settings.webapp_url))]]
    )
    await update.message.reply_text(
        "Раздел «Прогресс» (черновик). Графики — в MiniApp:",
        reply_markup=keyboard,
    )


def register(app: Application) -> None:
    app.add_handler(CommandHandler("progress", progress))
