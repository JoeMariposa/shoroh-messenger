import os
import sqlite3
import logging
import asyncio
import random
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ContextTypes, ConversationHandler,
    MessageHandler, filters, CallbackQueryHandler
)

# Логгирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN is not set!")
    raise ValueError("TELEGRAM_BOT_TOKEN is not set!")

AWAITING_LOG = 0

# --- DATABASE ---
def init_db():
    logger.info("Initializing database")
    conn = sqlite3.connect("logs.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS logs (id TEXT PRIMARY KEY, content TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS submissions (chat_id TEXT, content TEXT)")
    c.execute("INSERT OR IGNORE INTO logs (id, content) VALUES (?, ?)", ("LOG 01", "Transmission: Signal detected at 0300 hours."))
    c.execute("INSERT OR IGNORE INTO logs (id, content) VALUES (?, ?)", ("LOG 02", "Anomaly reported in sector 7."))
    c.execute("INSERT OR IGNORE INTO logs (id, content) VALUES (?, ?)", ("LOG 03", "Last contact with unit RED-9B at 1800."))
    conn.commit()
    conn.close()
    logger.info("Database initialized")

def get_latest_log():
    conn = sqlite3.connect("logs.db")
    c = conn.cursor()
    c.execute("SELECT content FROM logs WHERE id = 'LOG 03'")
    result = c.fetchone()
    conn.close()
    return result[0] if result else "Нет доступных логов."

def get_all_logs():
    conn = sqlite3.connect("logs.db")
    c = conn.cursor()
    c.execute("SELECT id, content FROM logs")
    logs = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    return logs

def save_submission(chat_id, text):
    conn = sqlite3.connect("logs.db")
    c = conn.cursor()
    c.execute("INSERT INTO submissions (chat_id, content) VALUES (?, ?)", (str(chat_id), text))
    conn.commit()
    conn.close()

# --- Варианты фраз ---
START_MESSAGES = [
    "Линия связи установлена. Терминал активен. Эфир шепчет.",
    "Сигнал захвачен. Ты в системе. Не прерывай канал.",
    "RX: соединение установлено. Логирование разрешено. Слушай внимательно."
]
ECHO_MESSAGES = [
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
LOG_MESSAGES = [
    "ЛОГ принят: {log}. Передача завершена.",
    "Последняя активность зафиксирована. Содержимое: {log}.",
    "Сигнал реконструирован. Транслирую последнюю запись…"
]
PULSE_MESSAGES = [
    "Варианты маршрута загружены. Решай, пока эфир не сорвался.",
    "Принять решение — уже движение. Выбери путь.",
    "Сектор разветвлён. Укажи направление: [вперёд | остаться | вернуться]."
]
CODE_SUCCESS_MESSAGES = [
    "Код принят. Активирован протокол ∆-209A. Ожидай отклика.",
    "Доступ подтверждён. Расшифровка началась.",
    "Сигнал принят. Ответ будет не для всех."
]
CODE_FAIL_MESSAGES = [
    "Ошибка. Код отрицается эфиром.",
    "Неверная последовательность. Отказ доступа.",
    "RX: ключ не принят. Сигнал отклонён."
]
ARCHIVE_MESSAGES = [
    "Открыт архив. Передачи отсортированы. Выбери.",
    "Доступ к архиву разрешён. Некоторые записи шифруются до сих пор.",
    "Архив логов активен. Перехваченные сигналы ждут расшифровки."
]
CAST_START_MESSAGES = [
    "Терминал готов. Передай, что ты слышал или видел.",
    "Эфир открыт для твоего сигнала. Говори.",
    "Начни передачу. Мы сохраним её."
]
CAST_SAVED_MESSAGES = [
    "Принято. Твоя запись вошла в эфир. Кто-то услышит.",
    "Лог сохранён. Назначен код временной метки.",
    "Передача завершена. Шорох сохранит."
]
HELP_MESSAGES = [
    "Команды терминала активны. Запросы слушаются.",
    "Доступные сигналы: /log /cast /pulse /echo /code /archive /start /scan.",
    "Это не просто команды. Это ключи. Используй их с умом."
]

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /start command from chat {update.effective_chat.id}")
    await update.message.reply_text(random.choice(START_MESSAGES))

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /echo command from chat {update.effective_chat.id}")
    await update.message.reply_text(random.choice(ECHO_MESSAGES))

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /log command from chat {update.effective_chat.id}")
    latest_log = get_latest_log()
    msg = random.choice(LOG_MESSAGES).format(log=latest_log)
    await update.message.reply_text(msg)

async def pulse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /pulse command from chat {update.effective_chat.id}")
    await update.message.reply_text(random.choice(PULSE_MESSAGES))
    keyboard = [
        [
            InlineKeyboardButton("Вперед", callback_data="vote_forward"),
            InlineKeyboardButton("Остаться", callback_data="vote_stay"),
            InlineKeyboardButton("Вернуться", callback_data="vote_back")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Варианты направления:",
        reply_markup=reply_markup
    )

async def code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /code command from chat {update.effective_chat.id}")
    code = " ".join(context.args) if context.args else ""
    if code == "D-209A":
        await update.message.reply_text(random.choice(CODE_SUCCESS_MESSAGES))
    else:
        await update.message.reply_text(random.choice(CODE_FAIL_MESSAGES))

async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /archive command from chat {update.effective_chat.id}")
    logs = get_all_logs()
    await update.message.reply_text(random.choice(ARCHIVE_MESSAGES))
    keyboard = [[InlineKeyboardButton(log, callback_data=log)] for log in logs.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Доступные архивные логи:", reply_markup=reply_markup)

async def cast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /cast command from chat {update.effective_chat.id}")
    await update.message.reply_text(random.choice(CAST_START_MESSAGES))
    return AWAITING_LOG

async def save_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Saving log from chat {update.effective_chat.id}")
    chat_id = update.effective_chat.id
    save_submission(chat_id, update.message.text)
    await update.message.reply_text(random.choice(CAST_SAVED_MESSAGES))
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /cancel command from chat {update.effective_chat.id}")
    await update.message.reply_text("Передача отменена.")
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /help command from chat {update.effective_chat.id}")
    await update.message.reply_text(random.choice(HELP_MESSAGES))

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received unknown command from chat {update.effective_chat.id}")
    await update.message.reply_text("Неизвестная команда. Используйте /help.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    logger.info(f"Received callback query: {data}")
    await query.answer()
    logs = get_all_logs()
    if data.startswith("vote_"):
        vote = data.split("_")[1].capitalize()
        await query.message.reply_text(f"Голос учтён: {vote}")
    elif data in logs:
        await query.message.reply_text(f"{data}: {logs[data]}")

# --- FLASK + PTB WEBHOOK ---
app_flask = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# --- РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ ---
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("echo", echo))
application.add_handler(CommandHandler("log", log))
application.add_handler(CommandHandler("pulse", pulse))
application.add_handler(CommandHandler("code", code))
application.add_handler(CommandHandler("archive", archive))
application.add_handler(CommandHandler("help", help_command))

application.add_handler(ConversationHandler(
    entry_points=[CommandHandler("cast", cast)],
    states={AWAITING_LOG: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_log)]},
    fallbacks=[CommandHandler("cancel", cancel)]
))

application.add_handler(CallbackQueryHandler(handle_callback))

# ОБРАБОТЧИК ДОЛЖЕН БЫТЬ ПОСЛЕДНИМ!
application.add_handler(MessageHandler(filters.COMMAND, unknown))

@app_flask.route("/", methods=["GET"])
def index():
    logger.info("Received request to /")
    return "Bot is running."

@app_flask.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    try:
        logger.info("Received webhook request")
        data = request.get_json(force=True)
        if not data:
            logger.info("Empty webhook request")
            return "ok"
        update = Update.de_json(data, application.bot)
        if update:
            logger.info(f"Processing update: {update}")
            asyncio.run(application.process_update(update))
        else:
            logger.info("No update found in request")
        return "ok"
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "ok", 500

if __name__ == "__main__":
    init_db()
    logger.info("Starting bot with webhook")
    app_flask.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))