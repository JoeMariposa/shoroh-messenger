import logging
import random
import os
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
import sqlite3

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Проверка токена
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set!")

app_flask = Flask(__name__)

# SQLite
def init_db():
    conn = sqlite3.connect("logs.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS logs (id TEXT PRIMARY KEY, content TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS submissions (chat_id TEXT, content TEXT)")
    conn.commit()
    conn.close()

def get_latest_log():
    conn = sqlite3.connect("logs.db")
    c = conn.cursor()
    c.execute("SELECT content FROM logs ORDER BY rowid DESC LIMIT 1")
    result = c.fetchone()
    conn.close()
    return result[0] if result else "Нет логов"

def save_submission(chat_id, text):
    conn = sqlite3.connect("logs.db")
    c = conn.cursor()
    c.execute("INSERT INTO submissions (chat_id, content) VALUES (?, ?)", (str(chat_id), text))
    conn.commit()
    conn.close()

# Ответы
RESPONSES = {
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
        "ЛОГ принят: (пост Лога из канала). Передача завершена.",
        "Последняя активность зафиксирована. Содержимое: {лог}.",
        "Сигнал реконструирован. Транслирую последнюю запись…"
    ],
    "pulse": [
        "Варианты маршрута загружены. Решай, пока эфир не сорвался.",
        "Принять решение — уже движение. Выбери путь.",
        "Сектор разветвлён. Укажи направление: [вперёд | остаться | вернуться]."
    ],
    "help": [
        "Команды терминала активны. Запросы слушаются.",
        "Доступные сигналы: /log /cast /pulse /echo /code /archive /start /scan.",
        "Это не просто команды. Это ключи. Используй их с умом."
    ],
    "archive": [
        "Открыт архив. Передачи отсортированы. Выбери.",
        "Доступ к архиву разрешён. Некоторые записи шифруются до сих пор.",
        "Архив логов активен. Перехваченные сигналы ждут расшифровки."
    ],
    "cast_prompt": [
        "Терминал готов. Передай, что ты слышал или видел.",
        "Эфир открыт для твоего сигнала. Говори.",
        "Начни передачу. Мы сохраним её."
    ],
    "cast_received": [
        "Принято. Твоя запись вошла в эфир. Кто-то услышит.",
        "Лог сохранён. Назначен код временной метки.",
        "Передача завершена. Шорох сохранит."
    ]
}

AWAITING_CAST = 0

# Обработчики
async def random_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str):
    logger.info(f"Command /{command} received from {update.message.from_user.id}")
    await update.message.reply_text(random.choice(RESPONSES[command]))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await random_reply(update, context, "start")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await random_reply(update, context, "echo")

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    latest_log = get_latest_log()
    response = random.choice(RESPONSES["log"]).format(лог=latest_log)
    await update.message.reply_text(response)

async def pulse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Вперед", callback_data="vote_forward"),
         InlineKeyboardButton("Остаться", callback_data="vote_stay"),
         InlineKeyboardButton("Вернуться", callback_data="vote_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(random.choice(RESPONSES["pulse"]), reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await random_reply(update, context, "help")

async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("LOG 01", callback_data="LOG 01"),
         InlineKeyboardButton("LOG 02", callback_data="LOG 02"),
         InlineKeyboardButton("LOG 03", callback_data="LOG 03")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(random.choice(RESPONSES["archive"]), reply_markup=reply_markup)

async def cast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(RESPONSES["cast_prompt"]))
    return AWAITING_CAST

async def handle_cast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    save_submission(chat_id, update.message.text)
    await update.message.reply_text(random.choice(RESPONSES["cast_received"]))
    return ConversationHandler.END

async def code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        code_input = context.args[0]
        if code_input == "секрет":
            await update.message.reply_text("Код принят. Активирован протокол ∆-209A. Ожидай отклика.")
        else:
            await update.message.reply_text(random.choice([
                "Ошибка. Код отрицается эфиром.",
                "Неверная последовательность. Отказ доступа.",
                "RX: ключ не принят. Сигнал отклонён."
            ]))
    else:
        await update.message.reply_text("Введите код после команды. Пример: /code секрет")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("vote_"):
        vote = data.split("_")[1].capitalize()
        await query.message.reply_text(f"Голос учтён: {vote}")
    elif data in ["LOG 01", "LOG 02", "LOG 03"]:
        await query.message.reply_text(f"{data}: Transmission test")

# Инициализация
init_db()
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("echo", echo))
app.add_handler(CommandHandler("log", log))
app.add_handler(CommandHandler("pulse", pulse))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("archive", archive))
app.add_handler(CommandHandler("cast", cast))
app.add_handler(CommandHandler("code", code))
app.add_handler(ConversationHandler(
    entry_points=[CommandHandler("cast", cast)],
    states={AWAITING_CAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_cast_message)]},
    fallbacks=[]
))
app.add_handler(CallbackQueryHandler(button_callback))

# Webhook для Render
@app_flask.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(), app.bot)
    await app.process_update(update)
    return "ok"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app_flask, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    main()

