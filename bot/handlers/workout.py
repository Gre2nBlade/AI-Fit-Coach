"""/workout — генерация и просмотр тренировок.

Черновик: вместо ConversationHandler — простые команды и кнопки.
"""
from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes


async def workout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⚡ Сгенерировать план", callback_data="workout:generate")],
            [InlineKeyboardButton("📋 Мои планы", callback_data="workout:list")],
            [InlineKeyboardButton("✅ Записать результат", callback_data="workout:log")],
        ]
    )
    await update.message.reply_text("Раздел «Тренировка» (черновик):", reply_markup=keyboard)


def register(app: Application) -> None:
    app.add_handler(CommandHandler("workout", workout))
    # TODO: CallbackQueryHandler на workout:* → services.workout_service
