import os
import random
import logging
import asyncio
import requests
from flask import Flask, request, Response
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, CallbackQueryHandler
)

# --- Чтение переменных окружения ---
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
WEBHOOK_HOST = "https://shoroh-messenger.onrender.com"
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# --- Flask и PTB Application ---
app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# --- Вариативные ответы для команд ---
START_REPLIES = [
    "Линия связи установлена. Терминал активен. Эфир шепчет.",
    "Сигнал захвачен. Ты в системе. Не прерывай канал.",
    "RX: соединение установлено. Логирование разрешено. Слушай внимательно.",
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

LOG_REPLIES = [
    "ЛОГ принят: (пост Лога из канала). Передача завершена.",
    "Последняя активность зафиксирована. Содержимое: {лог}.",
    "Сигнал реконструирован. Транслирую последнюю запись…"
]

PULSE_REPLIES = [
    "Варианты маршрута загружены. Решай, пока эфир не сорвался.",
    "Принять решение — уже движение. Выбери путь.",
    "Сектор разветвлён. Укажи направление: [вперёд | остаться | вернуться]."
]

CODE_OK = [
    "Код принят. Активирован протокол ∆-209A. Ожидай отклика.",
    "Доступ подтверждён. Расшифровка началась.",
    "Сигнал принят. Ответ будет не для всех."
]
CODE_FAIL = [
    "Ошибка. Код отрицается эфиром.",
    "Неверная последовательность. Отказ доступа.",
    "RX: ключ не принят. Сигнал отклонён."
]

ARCHIVE_REPLIES = [
    "Открыт архив. Передачи отсортированы. Выбери.",
    "Доступ к архиву разрешён. Некоторые записи шифруются до сих пор.",
    "Архив логов активен. Перехваченные сигналы ждут расшифровки."
]

CAST_READY = [
    "Терминал готов. Передай, что ты слышал или видел.",
    "Эфир открыт для твоего сигнала. Говори.",
    "Начни передачу. Мы сохраним её."
]
CAST_DONE = [
    "Принято. Твоя запись вошла в эфир. Кто-то услышит.",
    "Лог сохранён. Назначен код временной метки.",
    "Передача завершена. Шорох сохранит."
]

HELP_REPLIES = [
    "Команды терминала активны. Запросы слушаются.",
    "Доступные сигналы: /log /cast /pulse /echo /code /archive /start /scan.",
    "Это не просто команды. Это ключи. Используй их с умом."
]

# --- Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(START_REPLIES))

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(ECHO_REPLIES))

async def log_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Здесь можно заменить на фактическое получение лога
    log_text = "Содержимое последнего лога"
    reply = random.choice(LOG_REPLIES).replace("{лог}", log_text)
    await update.message.reply_text(reply)

async def pulse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = random.choice(PULSE_REPLIES)
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Вперёд", callback_data="route_forward"),
            InlineKeyboardButton("Остаться", callback_data="route_stay"),
            InlineKeyboardButton("Вернуться", callback_data="route_back")
        ]
    ])
    await update.message.reply_text(reply, reply_markup=keyboard)

async def code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args and context.args[0] == "209A":  # пример кода
        await update.message.reply_text(random.choice(CODE_OK))
    else:
        await update.message.reply_text(random.choice(CODE_FAIL))

async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(ARCHIVE_REPLIES))

async def cast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(CAST_READY))
    context.user_data["casting"] = True

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(HELP_REPLIES))

async def handle_cast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("casting"):
        await update.message.reply_text(random.choice(CAST_DONE))
        context.user_data["casting"] = False

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    routes = {
        "route_forward": "Ты выбрал путь вперёд.",
        "route_stay": "Ты решил остаться.",
        "route_back": "Маршрут: возвращение.",
    }
    await query.edit_message_text(routes.get(query.data, "Выбор не распознан."))

# --- Регистрация хэндлеров ---
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("echo", echo))
application.add_handler(CommandHandler("log", log_cmd))
application.add_handler(CommandHandler("pulse", pulse))
application.add_handler(CommandHandler("code", code))
application.add_handler(CommandHandler("archive", archive))
application.add_handler(CommandHandler("cast", cast))
application.add_handler(CommandHandler("help", help_cmd))
application.add_handler(CallbackQueryHandler(button))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_cast_message))

# --- WEBHOOK endpoint ---
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.run(application.process_update(update))
    return Response("ok", status=200)

# --- Webhook set при запуске ---
def set_webhook():
    resp = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/setWebhook",
        json={"url": WEBHOOK_URL}
    )
    logging.info("Webhook set: %s", resp.text)

# --- Запуск приложения ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    set_webhook()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)