"""/nutrition — дневник питания. Черновик: команда + кнопки."""
from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes


async def nutrition(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("➕ Добавить приём пищи", callback_data="nutrition:add")],
            [InlineKeyboardButton("📖 Дневник", callback_data="nutrition:diary")],
            [InlineKeyboardButton("🧮 Рассчитать КБЖУ", callback_data="nutrition:calc")],
        ]
    )
    await update.message.reply_text("Раздел «Питание» (черновик):", reply_markup=keyboard)


def register(app: Application) -> None:
    app.add_handler(CommandHandler("nutrition", nutrition))
    # TODO: CallbackQueryHandler на nutrition:* → services.nutrition_service
