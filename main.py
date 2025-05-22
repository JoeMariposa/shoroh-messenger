from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import os
import random
import nest_asyncio

nest_asyncio.apply()  # Allow nested event loops if needed

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
app = Flask(__name__)

# In-memory storage for logs and user submissions
LOGS = {
    "LOG 01": "Transmission: Signal detected at 0300 hours.",
    "LOG 02": "Anomaly reported in sector 7.",
    "LOG 03": "Last contact with unit RED-9B at 1800."
}
USER_SUBMISSIONS = {}  # {chat_id: [user_logs]}

# Initialize the Telegram Application
application = Application.builder().token(TOKEN).build()

async def start(update: Update, context):
    await update.message.reply_text("Соединение установлено. Вы подключены к приёмнику RED-9B.")

async def echo(update: Update, context):
    if random.random() < 0.8:
        await update.message.reply_text("Связь стабильна. Помех: 1.3%. Переход возможен.")
    else:
        await update.message.reply_text("Пульсация нарушена. Предупреждение: активность слева.")

async def log(update: Update, context):
    latest_log = LOGS.get("LOG 03", "Нет доступных логов.")
    await update.message.reply_text(f"Последняя передача: {latest_log}")

async def pulse(update: Update, context):
    keyboard = [
        [
            InlineKeyboardButton("Вперед", callback_data="vote_forward"),
            InlineKeyboardButton("Остаться", callback_data="vote_stay"),
            InlineKeyboardButton("Вернуться", callback_data="vote_back")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Визуальный выбор: Куда пойдёт сталкер?", reply_markup=reply_markup)

async def code(update: Update, context):
    code = " ".join(context.args).strip()
    if code == "D-209A":
        await update.message.reply_text("Код принят. Спец-лог: Секретный сигнал RED-9B активирован.")
    else:
        await update.message.reply_text("Сбой: Неверный код.")

async def archive(update: Update, context):
    keyboard = [[InlineKeyboardButton(log, callback_data=log)] for log in LOGS.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Доступные архивные логи:", reply_markup=reply_markup)

async def frequency(update: Update, context):
    USER_SUBMISSIONS[update.message.chat_id] = []
    await update.message.reply_text("Хотите передать свою запись в эфир? Опишите, что вы видели или слышали.")

async def help_cmd(update: Update, context):
    help_text = (
        "/вход — Подключиться к эфиру\n"
        "/эхо — Проверка сигнала\n"
        "/лог — Последняя передача\n"
        "/пульс — Голосование за направление\n"
        "/код — Ввод скрытого сигнала\n"
        "/архив — Доступ к архивным логам\n"
        "/частота — Отправка собственного лога\n"
        "/помощь — Справка по командам"
    )
    await update.message.reply_text(help_text)

async def handle_submission(update: Update, context):
    chat_id = update.message.chat_id
    if chat_id in USER_SUBMISSIONS and USER_SUBMISSIONS[chat_id] is not None:
        USER_SUBMISSIONS[chat_id].append(update.message.text)
        await update.message.reply_text("Ваша запись сохранена в эфире.")
        USER_SUBMISSIONS[chat_id] = None

async def callback_query(update: Update, context):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("vote_"):
        vote = query.data.split("_")[1].capitalize()
        await query.message.reply_text(f"Голос учтён: {vote}")
    elif query.data in LOGS:
        await query.message.reply_text(f"{query.data}: {LOGS[query.data]}")

# Register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("echo", echo))
application.add_handler(CommandHandler("log", log))
application.add_handler(CommandHandler("pulse", pulse))
application.add_handler(CommandHandler("code", code))
application.add_handler(CommandHandler("archive", archive))
application.add_handler(CommandHandler("cast", cast))
application.add_handler(CommandHandler("help", help_command))


@app.route(f"/{TOKEN}", methods=["POST"])
async def receive_update():
    try:
        update = Update.de_json(request.get_json(), application.bot)
        await application.process_update(update)
        return "ok"
    except Exception as e:
        print(f"Error: {e}")
        return "ok"

@app.route("/", methods=["GET"])
def index():
    return "Bot is running."

if __name__ == "__main__":
    import uvicorn
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        url_path=f"/{TOKEN}",
        webhook_url=f"https://<your-app>.onrender.com/{TOKEN}"
    )
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))



