"""Настройка напоминаний пользователем. Черновик: кнопки вкл/выкл."""
from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes


async def notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔔 Включить напоминания", callback_data="notify:on")],
            [InlineKeyboardButton("🔕 Выключить", callback_data="notify:off")],
        ]
    )
    await update.message.reply_text("Раздел «Напоминания» (черновик):", reply_markup=keyboard)


def register(app: Application) -> None:
    app.add_handler(CommandHandler("notifications", notifications))
    # TODO: CallbackQueryHandler на notify:* → services.scheduler
