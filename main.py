import logging
import random
import sqlite3
import asyncio

from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

TOKEN = "ВАШ_ТОКЕН"  # Замените на токен вашего бота
WEBHOOK_PATH = f"/webhook/{TOKEN}"
DB_PATH = "shoroh.sqlite"

REPLIES = {
    "start": [
        "Линия связи установлена. Терминал активен. Эфир шепчет.",
        "Сигнал захвачен. Ты в системе. Не прерывай канал.",
        "RX: соединение установлено. Логирование разрешено. Слушай внимательно.",
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
        "RX: возврат сигнала подтверждён. Исходная точка не совпадает.",
    ],
    "log": [
        "ЛОГ принят: {log}. Передача завершена.",
        "Последняя активность зафиксирована. Содержимое: {log}.",
        "Сигнал реконструирован. Транслирую последнюю запись…",
    ],
    "pulse": [
        "Варианты маршрута загружены. Решай, пока эфир не сорвался.",
        "Принять решение — уже движение. Выбери путь.",
        "Сектор разветвлён. Укажи направление: [вперёд | остаться | вернуться].",
    ],
    "code_ok": [
        "Код принят. Активирован протокол ∆-209A. Ожидай отклика.",
        "Доступ подтверждён. Расшифровка началась.",
        "Сигнал принят. Ответ будет не для всех.",
    ],
    "code_fail": [
        "Ошибка. Код отрицается эфиром.",
        "Неверная последовательность. Отказ доступа.",
        "RX: ключ не принят. Сигнал отклонён.",
    ],
    "archive": [
        "Открыт архив. Передачи отсортированы. Выбери.",
        "Доступ к архиву разрешён. Некоторые записи шифруются до сих пор.",
        "Архив логов активен. Перехваченные сигналы ждут расшифровки.",
    ],
    "cast_ready": [
        "Терминал готов. Передай, что ты слышал или видел.",
        "Эфир открыт для твоего сигнала. Говори.",
        "Начни передачу. Мы сохраним её.",
    ],
    "cast_done": [
        "Принято. Твоя запись вошла в эфир. Кто-то услышит.",
        "Лог сохранён. Назначен код временной метки.",
        "Передача завершена. Шорох сохранит.",
    ],
    "help": [
        "Команды терминала активны. Запросы слушаются.",
        "Доступные сигналы: /log /cast /pulse /echo /code /archive /start /scan.",
        "Это не просто команды. Это ключи. Используй их с умом.",
    ],
    "unknown": [
        "Неизвестная команда. Используйте /help."
    ]
}

# --------- ИНИЦИАЛИЗАЦИЯ ---------
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO
)

app_flask = Flask(__name__)
application = Application.builder().token(TOKEN).build()

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                log TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

init_db()

# --------- КОМАНДЫ ---------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES["start"]))

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES["echo"]))

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT log FROM logs ORDER BY timestamp DESC LIMIT 1")
        result = c.fetchone()
        log_txt = result[0] if result else "нет новых логов."
    text = random.choice(REPLIES["log"]).format(log=log_txt)
    await update.message.reply_text(text)

async def pulse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES["pulse"]))

async def code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Укажите код после /code.")
        return
    user_code = context.args[0].strip().lower()
    secret_codes = {"delta209a", "209a", "secretkey"}
    if user_code in secret_codes:
        await update.message.reply_text(random.choice(REPLIES["code_ok"]))
    else:
        await update.message.reply_text(random.choice(REPLIES["code_fail"]))

async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES["archive"]))

async def cast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['awaiting_log'] = True
    await update.message.reply_text(random.choice(REPLIES["cast_ready"]))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "\n".join(REPLIES["help"])
    await update.message.reply_text(text)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(REPLIES["unknown"][0])

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_log'):
        log_txt = update.message.text
        user_id = update.effective_user.id
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO logs (user_id, log) VALUES (?, ?)", (user_id, log_txt))
            conn.commit()
        context.user_data['awaiting_log'] = False
        await update.message.reply_text(random.choice(REPLIES["cast_done"]))
    else:
        await unknown(update, context)

# --------- HANDLERS ---------
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("echo", echo))
application.add_handler(CommandHandler("log", log))
application.add_handler(CommandHandler("pulse", pulse))
application.add_handler(CommandHandler("code", code))
application.add_handler(CommandHandler("archive", archive))
application.add_handler(CommandHandler("cast", cast))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("scan", help_command))  # Если нужно
# application.add_handler(CommandHandler("unknown", unknown)) # Не нужен, unknown ловится фильтром

# Неизвестная команда:
application.add_handler(MessageHandler(filters.COMMAND, unknown))
# Текстовое сообщение:
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# --------- FLASK WEBHOOK ---------
@app_flask.route("/", methods=["GET"])
def index():
    return "OK"

@app_flask.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(application.process_update(update))
    except RuntimeError:
        asyncio.run(application.process_update(update))
    return "ok"

if __name__ == "__main__":
    logging.info("Initializing database")
    init_db()
    logging.info("Database initialized")
    logging.info("Starting bot with webhook")
    app_flask.run(host="0.0.0.0", port=10000)