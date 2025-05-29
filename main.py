import os
import logging
import random
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes
)
import asyncio

TOKEN = os.getenv("TELEGRAM_TOKEN", "7834724747:AAEEojrbLDsXht_mQu6oFbYK7OGTDcr5FpI")
WEBHOOK_PATH = f"/webhook/{TOKEN}"

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# --- Вариативные ответы ---
REPLIES = {
    "start": [
        "Привет! Я бот ShorohMessenger. Готов к передаче сообщений.",
        "Добро пожаловать! Используйте /help для просмотра доступных команд.",
        "Здравствуй, сталкер. Я на связи!"
    ],
    "help": [
        "Доступные команды: /start, /help, /cast, /echo.",
        "Справка: напишите /cast или /echo для теста.",
        "Используйте /start для запуска, /cast для передачи сигнала."
    ],
    "echo": [
        "Повторяю: {text}",
        "Вы сказали: {text}",
        "Эхо-ответ: {text}"
    ],
    "cast": [
        "Сигнал передан в эфир!",
        "Передача выполнена.",
        "Радиосообщение успешно отправлено."
    ],
    "unknown": [
        "Неизвестная команда. Используйте /help.",
        "Команда не распознана. Справка — команда /help.",
        "Извините, я не понимаю эту команду."
    ]
}

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['start']))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['help']))

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(random.choice(REPLIES['echo']).format(text=text))

async def cast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['cast']))

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['unknown']))

# --- Application ---
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("echo", echo))
application.add_handler(CommandHandler("cast", cast))

# Для неизвестных команд — обработка через MessageHandler, а не CommandHandler!
from telegram.ext import MessageHandler, filters
application.add_handler(MessageHandler(filters.COMMAND, unknown))

# --- Flask routes ---
@app.route("/", methods=["GET"])
def index():
    return "OK"

@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.run(application.process_update(update))
    return "OK"

# --- Запуск ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)