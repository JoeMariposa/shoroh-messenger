import os
import random
import sqlite3
import logging
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
)

# --- Настройки ---
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN')  # Указать токен через переменную среды!
DB_NAME = 'logs.db'
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Инициализация Flask ---
app_flask = Flask(__name__)

# --- Telegram Application (PTB 20.x) ---
application = Application.builder().token(TOKEN).concurrent_updates(True).build()
application_initialized = False

# --- Сообщения для вариативности ---
REPLIES = {
    "start": [
        "Линия связи установлена. Терминал активен. Эфир шепчет.",
        "Сигнал захвачен. Ты в системе. Не прерывай канал.",
        "RX: соединение установлено. Логирование разрешено. Слушай внимательно."
    ],
    "echo": [
        "Связь стабильна. Уровень шума: 2.1 дБ. Продолжай.",
        "Ответ получен. Эхо отражено. Канал чист.",
        "Пульсация зафиксирована. Отголосок принят.",
        "Связь стабильна. Уровень шума: 2.3 дБ. Приём продолжается.",
        "Ответ получен. Источник не идентифицирован.",
        "Канал зафиксирован. Чужой отклик на частоте 147.9 МГц.",
        "Шорох на линии. Ты уверен, что это был тест?",
        "Проверка завершена. Но эхо продолжает звучать.",
        "RX: возврат сигнала подтверждён. Исходная точка не совпадает."
    ],
    "log": [
        "ЛОГ принят: {log}. Передача завершена.",
        "Последняя активность зафиксирована. Содержимое: {log}.",
        "Сигнал реконструирован. Транслирую последнюю запись…\n{log}"
    ],
    "pulse": [
        "Варианты маршрута загружены. Решай, пока эфир не сорвался.",
        "Принять решение — уже движение. Выбери путь.",
        "Сектор разветвлён. Укажи направление: [вперёд | остаться | вернуться]."
    ],
    "archive": [
        "Открыт архив. Передачи отсортированы. Выбери.",
        "Доступ к архиву разрешён. Некоторые записи шифруются до сих пор.",
        "Архив логов активен. Перехваченные сигналы ждут расшифровки."
    ],
    "cast_init": [
        "Терминал готов. Передай, что ты слышал или видел.",
        "Эфир открыт для твоего сигнала. Говори.",
        "Начни передачу. Мы сохраним её."
    ],
    "cast_done": [
        "Принято. Твоя запись вошла в эфир. Кто-то услышит.",
        "Лог сохранён. Назначен код временной метки.",
        "Передача завершена. Шорох сохранит."
    ],
    "help": [
        "Команды терминала активны. Запросы слушаются.\n\n"
        "Доступные сигналы: /log /cast /pulse /echo /code /archive /start /scan.",
        "Это не просто команды. Это ключи. Используй их с умом."
    ],
    "unknown": [
        "Неизвестная команда. Используйте /help."
    ]
}

# --- Простая SQLite логика (если нужна для хранения логов) ---
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT, ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )

def save_log(content):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO logs (content) VALUES (?)", (content,))

def get_latest_log():
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute("SELECT content FROM logs ORDER BY id DESC LIMIT 1").fetchone()
        return row[0] if row else "Нет логов."

def get_all_logs():
    with sqlite3.connect(DB_NAME) as conn:
        rows = conn.execute("SELECT id, content FROM logs ORDER BY id DESC LIMIT 10").fetchall()
        return [f"LOG {id:02d}: {content}" for id, content in rows]

# --- Хендлеры команд ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['start']))

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['echo']))

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log = get_latest_log()
    text = random.choice(REPLIES['log']).format(log=log)
    await update.message.reply_text(text)

async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['archive']))
    logs = get_all_logs()
    keyboard = [
        [InlineKeyboardButton(log, callback_data=f"log_{i+1}")]
        for i, log in enumerate(logs)
    ]
    if keyboard:
        await update.message.reply_text("Выберите лог:", reply_markup=InlineKeyboardMarkup(keyboard))

async def pulse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = random.choice(REPLIES['pulse'])
    keyboard = [
        [
            InlineKeyboardButton("Вперёд", callback_data="forward"),
            InlineKeyboardButton("Остаться", callback_data="stay"),
            InlineKeyboardButton("Вернуться", callback_data="back"),
        ]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# Для /cast – диалог (ConversationHandler)
from telegram.ext import ConversationHandler

CAST_MESSAGE = range(1)

async def cast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['cast_init']))
    return CAST_MESSAGE

async def cast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_log(update.message.text)
    await update.message.reply_text(random.choice(REPLIES['cast_done']))
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отмена передачи.")
    return ConversationHandler.END

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for text in REPLIES['help']:
        await update.message.reply_text(text)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['unknown']))

# --- Inline-кнопки и callback ---
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("log_"):
        idx = int(data[4:]) - 1
        logs = get_all_logs()
        if 0 <= idx < len(logs):
            await query.edit_message_text(logs[idx])
    elif data in ["forward", "stay", "back"]:
        route = {"forward": "Вперёд", "stay": "Остаться", "back": "Вернуться"}[data]
        await query.edit_message_text(f"Голос учтён: {route}")

# --- Flask + PTB Integration ---
@app_flask.before_first_request
def before_first_request_func():
    global application_initialized
    if not application_initialized:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(application.initialize())
        application_initialized = True
        logger.info("PTB Application initialized!")

@app_flask.route("/", methods=["GET"])
def index():
    return "Bot is running."

@app_flask.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    global application_initialized
    if not application_initialized:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(application.initialize())
        application_initialized = True

    update = Update.de_json(request.get_json(force=True), application.bot)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(application.process_update(update))
    return "ok"

# --- Регистрация хендлеров PTB ---
def register_handlers():
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("echo", echo))
    application.add_handler(CommandHandler("log", log))
    application.add_handler(CommandHandler("archive", archive))
    application.add_handler(CommandHandler("pulse", pulse))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CallbackQueryHandler(button))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('cast', cast_start)],
        states={
            CAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, cast_message)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
    application.add_handler(conv_handler)

    application.add_handler(MessageHandler(filters.COMMAND, unknown))

# --- Точка входа ---
if __name__ == "__main__":
    init_db()
    register_handlers()
    logger.info("Starting bot with webhook (Flask+PTB)")
    app_flask.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))