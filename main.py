import logging
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import os

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Соединение установлено. Вы подключены к приёмнику RED-9B.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import random
    if random.random() > 0.7:
        await update.message.reply_text("Пульсация нарушена. Предупреждение: активность слева.")
    else:
        await update.message.reply_text("Связь стабильна. Помех: 1.3%. Переход возможен.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands = (
        "/вход — Подключиться к эфиру\n"
        "/эхо — Проверка сигнала\n"
        "/лог — Последний ЛОГ\n"
        "/пульс — Голосование\n"
        "/код — Ввод скрытого сигнала\n"
        "/архив — Доступ к архиву\n"
        "/частота — Трансляция\n"
        "/помощь — Справка по командам"
    )
    await update.message.reply_text(commands)

# Flask endpoint
@app.route('/')
def index():
    return "Bot is running."

# Запуск бота
async def run_bot():
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("вход", start))
    app_bot.add_handler(CommandHandler("эхо", echo))
    app_bot.add_handler(CommandHandler("помощь", help_command))
    await app_bot.initialize()
    await app_bot.start()
    await app_bot.updater.start_polling()
    return app_bot

import asyncio
asyncio.run(run_bot())
