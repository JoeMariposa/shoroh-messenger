import os
import logging
import requests
import asyncio
import random
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_HOST = os.environ["WEBHOOK_HOST"]
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# --- Варианты реплик ---
START_REPLIES = [
    "Линия связи установлена. Терминал активен. Эфир шепчет.",
    "Сигнал захвачен. Ты в системе. Не прерывай канал.",
    "RX: соединение установлено. Логирование разрешено. Слушай внимательно."
]

ECHO_REPLIES = [
    "Связь стабильна. Уровень шума: 2.1 дБ. Продолжай.",
    "Ответ получен. Эхо отражено. Канал чист.",
    "Пульсация зафиксирована. Отголосок принят.",
    "Связь стабильна. Уровень шума: 2.3 дБ. Приём продолжается.",
    "Ответ получен. Источник не идентифицирован.",
    "Канал зафиксирован. Чужой отклик на частоте 147.9 МГц.",
    "Шорох на линии. Ты уверен, что это был тест?",
    "Проверка завершена. Но эхо продолжает звучать.",
    "RX: возврат сигнала подтверждён. Исходная точка не совпадает."
]

CAST_INIT_REPLIES = [
    "Терминал готов. Передай, что ты слышал или видел.",
    "Эфир открыт для твоего сигнала. Говори.",
    "Начни передачу. Мы сохраним её."
]

CAST_SAVE_REPLIES = [
    "Принято. Твоя запись вошла в эфир. Кто-то услышит.",
    "Лог сохранён. Назначен код временной метки.",
    "Передача завершена. Шорох сохранит."
]

# --- Стейты для ConversationHandler ---
CAST = range(1)

# --- Команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(START_REPLIES))

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(ECHO_REPLIES))

async def cast_init(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(CAST_INIT_REPLIES))
    return CAST

async def cast_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Можно сохранять сообщение в БД, сейчас только ответ
    await update.message.reply_text(random.choice(CAST_SAVE_REPLIES))
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Передача отменена. Эфир прерван.")
    return ConversationHandler.END

# --- Роутинг ---
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("echo", echo))

cast_conv = ConversationHandler(
    entry_points=[CommandHandler("cast", cast_init)],
    states={
        CAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, cast_save)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)
application.add_handler(cast_conv)

# --- Webhook endpoint ---
@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)

    async def process():
        if not application.running:
            await application.initialize()
        await application.process_update(update)

    asyncio.get_event_loop().create_task(process())
    return "ok"

if __name__ == "__main__":
    # Установка webhook
    webhook_url = f"{WEBHOOK_HOST}/webhook/{TOKEN}"
    res = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/setWebhook",
        data={"url": webhook_url}
    )
    logger.info(f"Webhook set: {res.text}")
    app.run(host="0.0.0.0", port=PORT)