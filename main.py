import os
import random
import logging
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
)

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN") or "7834724747:AAEEojrbLDsXht_mQu6oFbYK7OGTDcr5FpI"
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("WEBHOOK_URL")
if WEBHOOK_URL and WEBHOOK_URL.endswith("/"):
    WEBHOOK_URL = WEBHOOK_URL[:-1]
WEBHOOK_FULL = f"{WEBHOOK_URL}{WEBHOOK_PATH}" if WEBHOOK_URL else None

app = Flask(__name__)

# --- Вариативные реплики ---
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
        "ЛОГ принят: (пост Лога из канала). Передача завершена.",
        "Последняя активность зафиксирована. Содержимое: {лог}.",
        "Сигнал реконструирован. Транслирую последнюю запись…"
    ],
    "pulse": [
        "Варианты маршрута загружены. Решай, пока эфир не сорвался.",
        "Принять решение — уже движение. Выбери путь.",
        "Сектор разветвлён. Укажи направление: [вперёд | остаться | вернуться]."
    ],
    "code_true": [
        "Код принят. Активирован протокол ∆-209A. Ожидай отклика.",
        "Доступ подтверждён. Расшифровка началась.",
        "Сигнал принят. Ответ будет не для всех."
    ],
    "code_false": [
        "Ошибка. Код отрицается эфиром.",
        "Неверная последовательность. Отказ доступа.",
        "RX: ключ не принят. Сигнал отклонён."
    ],
    "archive": [
        "Открыт архив. Передачи отсортированы. Выбери.",
        "Доступ к архиву разрешён. Некоторые записи шифруются до сих пор.",
        "Архив логов активен. Перехваченные сигналы ждут расшифровки."
    ],
    "cast_before": [
        "Терминал готов. Передай, что ты слышал или видел.",
        "Эфир открыт для твоего сигнала. Говори.",
        "Начни передачу. Мы сохраним её."
    ],
    "cast_after": [
        "Принято. Твоя запись вошла в эфир. Кто-то услышит.",
        "Лог сохранён. Назначен код временной метки.",
        "Передача завершена. Шорох сохранит."
    ],
    "help": [
        "Команды терминала активны. Запросы слушаются.",
        "Доступные сигналы: /log /cast /pulse /echo /code /archive /start /scan.",
        "Это не просто команды. Это ключи. Используй их с умом."
    ],
}

# --- Инлайн-кнопки ---
def get_pulse_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Вперёд", callback_data="pulse_forward"),
            InlineKeyboardButton("Остаться", callback_data="pulse_stay"),
            InlineKeyboardButton("Вернуться", callback_data="pulse_back"),
        ]
    ])

def get_archive_keyboard():
    # Пример: 3 кнопки архива. Можно динамически
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Лог 1", callback_data="archive_1")],
        [InlineKeyboardButton("Лог 2", callback_data="archive_2")],
        [InlineKeyboardButton("Лог 3", callback_data="archive_3")],
    ])

# --- Хендлеры команд ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = random.choice(REPLIES["start"])
    await update.message.reply_text(text)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = random.choice(REPLIES["echo"])
    await update.message.reply_text(text)

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Можно подставлять актуальный лог сюда
    text = random.choice(REPLIES["log"]).replace("{лог}", "Нет новых логов.")
    await update.message.reply_text(text)

async def pulse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = random.choice(REPLIES["pulse"])
    await update.message.reply_text(text, reply_markup=get_pulse_keyboard())

async def code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args and context.args[0] == "209A":
        text = random.choice(REPLIES["code_true"])
    else:
        text = random.choice(REPLIES["code_false"])
    await update.message.reply_text(text)

async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = random.choice(REPLIES["archive"])
    await update.message.reply_text(text, reply_markup=get_archive_keyboard())

async def cast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ожидание следующего сообщения от пользователя
    text = random.choice(REPLIES["cast_before"])
    await update.message.reply_text(text)
    context.user_data["await_cast"] = True

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = random.choice(REPLIES["help"])
    await update.message.reply_text(text)

# Приём своего лога
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("await_cast"):
        text = random.choice(REPLIES["cast_after"])
        await update.message.reply_text(text)
        context.user_data["await_cast"] = False

# Обработка инлайн-кнопок
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("pulse_"):
        choice = query.data.replace("pulse_", "")
        await query.edit_message_text(f"Выбран маршрут: {choice.capitalize()}")
    elif query.data.startswith("archive_"):
        log_num = query.data.replace("archive_", "")
        await query.edit_message_text(f"Открыт архив Лог {log_num}.")

# --- Flask endpoint для webhook ---
@app.route("/")
def index():
    return "OK", 200

@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), None)
    application = app.application
    asyncio.create_task(application.process_update(update))
    return jsonify(success=True)

# --- Основной запуск бота ---
import asyncio

async def main():
    global application
    application = Application.builder().token(TOKEN).build()
    app.application = application

    # Хендлеры команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("echo", echo))
    application.add_handler(CommandHandler("log", log))
    application.add_handler(CommandHandler("pulse", pulse))
    application.add_handler(CommandHandler("code", code))
    application.add_handler(CommandHandler("archive", archive))
    application.add_handler(CommandHandler("cast", cast))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    if WEBHOOK_FULL:
        logger.info(f"Setting webhook to {WEBHOOK_FULL}")
        await application.bot.set_webhook(WEBHOOK_FULL)
    else:
        logger.error("WEBHOOK_URL не задан. Укажите RENDER_EXTERNAL_URL в настройках!")

if __name__ == "__main__":
    # Для асинхронного запуска main() до запуска Flask
    asyncio.run(main())
    app.run(host="0.0.0.0", port=10000)