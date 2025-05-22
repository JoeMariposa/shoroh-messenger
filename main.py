import sys
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
import os
import asyncio
import sqlite3
import logging
import random

# Логгирование
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Проверка токена
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN is not set!")
    raise ValueError("TELEGRAM_BOT_TOKEN is not set!")

app = Flask(__name__)

# Инициализация Telegram Application
telegram_app = Application.builder().token(TOKEN).build()

# Инициализация SQLite
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

# Состояние для ConversationHandler
AWAITING_LOG = 0

# Обработчики команд
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /start command from chat {update.effective_chat.id}")
    await update.message.reply_text(
        "Соединение установлено. Вы подключены к приёмнику RED-9B.\n"
        "Для помощи: /help"
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /echo command from chat {update.effective_chat.id}")
    if random.random() < 0.8:
        await update.message.reply_text("Связь стабильна. Помех: 1.3%. Переход возможен.")
    else:
        await update.message.reply_text("Пульсация нарушена. Предупреждение: активность слева.")

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /log command from chat {update.effective_chat.id}")
    latest_log = get_latest_log()
    await update.message.reply_text(f"Последняя передача: {latest_log}")

async def pulse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /pulse command from chat {update.effective_chat.id}")
    keyboard = [
        [
            InlineKeyboardButton("Вперед", callback_data="vote_forward"),
            InlineKeyboardButton("Остаться", callback_data="vote_stay"),
            InlineKeyboardButton("Вернуться", callback_data="vote_back")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Визуальный выбор: Куда пойдёт сталкер?",
        reply_markup=reply_markup
    )

async def code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /code command from chat {update.effective_chat.id}")
    code = " ".join(context.args) if context.args else ""
    if code == "D-209A":
        await update.message.reply_text("Код принят. Спец-лог: Секретный сигнал RED-9B активирован.")
    else:
        await update.message.reply_text("Сбой: Неверный код.")

async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /archive command from chat {update.effective_chat.id}")
    logs = get_all_logs()
    keyboard = [[InlineKeyboardButton(log, callback_data=log)] for log in logs.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Доступные архивные логи:", reply_markup=reply_markup)

async def cast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /cast command from chat {update.effective_chat.id}")
    await update.message.reply_text("Хотите передать свою запись в эфир? Опишите, что вы видели или слышали.")
    return AWAITING_LOG

async def save_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Saving log from chat {update.effective_chat.id}")
    chat_id = update.effective_chat.id
    save_submission(chat_id, update.message.text)
    await update.message.reply_text("Ваша запись сохранена в эфире.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /cancel command from chat {update.effective_chat.id}")
    await update.message.reply_text("Передача отменена.")
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /help command from chat {update.effective_chat.id}")
    help_text = (
        "/start — Подключиться к эфиру\n"
        "/echo — Проверка сигнала\n"
        "/log — Последняя передача\n"
        "/pulse — Голосование за направление\n"
        "/code <код> — Ввод скрытого сигнала\n"
        "/archive — Доступ к архивным логам\n"
        "/cast — Отправка собственного лога\n"
        "/help — Справка по командам"
    )
    await update.message.reply_text(help_text)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received unknown command from chat {update.effective_chat.id}")
    await update.message.reply_text("Неизвестная команда. Используйте /help.")

# Обработчик inline-кнопок
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

# Регистрация обработчиков
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("echo", echo))
telegram_app.add_handler(CommandHandler("log", log))
telegram_app.add_handler(CommandHandler("pulse", pulse))
telegram_app.add_handler(CommandHandler("code", code))
telegram_app.add_handler(CommandHandler("archive", archive))
telegram_app.add_handler(CommandHandler("help", help_command))
telegram_app.add_handler(MessageHandler(filters.COMMAND, unknown))
telegram_app.add_handler(ConversationHandler(
    entry_points=[CommandHandler("cast", cast)],
    states={AWAITING_LOG: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_log)]},
    fallbacks=[CommandHandler("cancel", cancel)]
))
telegram_app.add_handler(CallbackQueryHandler(handle_callback))

# Flask webhook (синхронная функция)
@app.route("/", methods=["GET"])
def index():
    logger.info("Received request to /")
    return "Bot is running."

@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    try:
        logger.info("Received webhook request")
        data = request.get_json(force=True)
        if not data:
            logger.info("Empty webhook request")
            return "ok"
        update = Update.de_json(data, telegram_app.bot)
        if update:
            logger.info(f"Processing update: {update}")
            loop = asyncio.get_event_loop()
            loop.run_until_complete(telegram_app.process_update(update))
        else:
            logger.info("No update found in request")
        return "ok"
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "ok"

# Запуск вебхука и бота
def set_webhook():
    logger.info("Setting webhook")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(telegram_app.bot.set_webhook(url=f"https://shoroh-messenger.onrender.com/webhook/{TOKEN}"))
    logger.info("Webhook set")

if __name__ == "__main__":
    init_db()
    set_webhook()
    logger.info("Starting bot with webhook")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

