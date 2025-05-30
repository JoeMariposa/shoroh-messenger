import os
import logging
import random
from flask import Flask, request, abort
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes,
    CallbackQueryHandler
)

# Логирование для отладки
logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем токен и host из окружения
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
WEBHOOK_HOST = os.environ.get("WEBHOOK_HOST")
if not BOT_TOKEN or not WEBHOOK_HOST:
    raise RuntimeError("Переменные окружения TELEGRAM_BOT_TOKEN и WEBHOOK_HOST обязательны!")

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

app = Flask(__name__)

# Варианты ответов для команд
REPLIES = {
    'start': [
        "Линия связи установлена. Терминал активен. Эфир шепчет.",
        "Сигнал захвачен. Ты в системе. Не прерывай канал.",
        "RX: соединение установлено. Логирование разрешено. Слушай внимательно."
    ],
    'echo': [
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
    'log': [
        "ЛОГ принят: (пост Лога из канала). Передача завершена.",
        "Последняя активность зафиксирована. Содержимое: {лог}.",
        "Сигнал реконструирован. Транслирую последнюю запись…"
    ],
    'pulse': [
        "Варианты маршрута загружены. Решай, пока эфир не сорвался.",
        "Принять решение — уже движение. Выбери путь.",
        "Сектор разветвлён. Укажи направление: [вперёд | остаться | вернуться]."
    ],
    'code_ok': [
        "Код принят. Активирован протокол ∆-209A. Ожидай отклика.",
        "Доступ подтверждён. Расшифровка началась.",
        "Сигнал принят. Ответ будет не для всех."
    ],
    'code_fail': [
        "Ошибка. Код отрицается эфиром.",
        "Неверная последовательность. Отказ доступа.",
        "RX: ключ не принят. Сигнал отклонён."
    ],
    'archive': [
        "Открыт архив. Передачи отсортированы. Выбери.",
        "Доступ к архиву разрешён. Некоторые записи шифруются до сих пор.",
        "Архив логов активен. Перехваченные сигналы ждут расшифровки."
    ],
    'cast_start': [
        "Терминал готов. Передай, что ты слышал или видел.",
        "Эфир открыт для твоего сигнала. Говори.",
        "Начни передачу. Мы сохраним её."
    ],
    'cast_done': [
        "Принято. Твоя запись вошла в эфир. Кто-то услышит.",
        "Лог сохранён. Назначен код временной метки.",
        "Передача завершена. Шорох сохранит."
    ],
    'help': [
        "Команды терминала активны. Запросы слушаются.",
        "Доступные сигналы: /log /cast /pulse /echo /code /archive /start /scan.",
        "Это не просто команды. Это ключи. Используй их с умом."
    ]
}

# Асинхронная инициализация приложения Telegram
application = Application.builder().token(BOT_TOKEN).build()

# ========== HANDLERS ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['start']))

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['echo']))

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Предположим, лог — это фиктивная строка
    log_content = "— пример лога —"
    template = random.choice(REPLIES['log'])
    await update.message.reply_text(template.replace("{лог}", log_content))

async def pulse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("Вперёд", callback_data='route_forward')],
        [InlineKeyboardButton("Остаться", callback_data='route_stay')],
        [InlineKeyboardButton("Вернуться", callback_data='route_back')],
    ]
    await update.message.reply_text(
        random.choice(REPLIES['pulse']),
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Допустим, архив — это меню (заглушка)
    buttons = [
        [InlineKeyboardButton("Лог 1", callback_data='archive_log1')],
        [InlineKeyboardButton("Лог 2", callback_data='archive_log2')],
        [InlineKeyboardButton("Лог 3", callback_data='archive_log3')],
    ]
    await update.message.reply_text(
        random.choice(REPLIES['archive']),
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def cast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['cast_start']))
    # Сохраняем статус пользователя, что он начал отправку (для продвинутой логики)

async def received_cast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Здесь можно добавить запись в базу
    await update.message.reply_text(random.choice(REPLIES['cast_done']))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('\n'.join(REPLIES['help']))

async def code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем аргумент
    if context.args and context.args[0] == "209A":
        await update.message.reply_text(random.choice(REPLIES['code_ok']))
    else:
        await update.message.reply_text(random.choice(REPLIES['code_fail']))

# inline-кнопки
async def inline_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith('route_'):
        routes = {
            'route_forward': "Двигаемся вперёд!",
            'route_stay': "Остаёмся на месте.",
            'route_back': "Возврат к предыдущей точке."
        }
        await query.edit_message_text(text=routes.get(query.data, "Выбран неизвестный маршрут."))
    elif query.data.startswith('archive_'):
        await query.edit_message_text(text=f"Запрошен {query.data.replace('archive_', 'архивный лог ')}.")

# "unknown command"
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Неизвестная команда. Воспользуйтесь /help.")

# ========== ROUTES ==========

@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        # Для PTB 20+ — синхронно через run_async
        application.create_task(application.process_update(update))
        return "OK", 200
    return abort(405)

@app.route("/", methods=["GET"])
def index():
    return "Шорох Messenger bot is up!", 200

# ========== MAIN ==========

def main():
    # Регистрация handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("echo", echo))
    application.add_handler(CommandHandler("log", log))
    application.add_handler(CommandHandler("pulse", pulse))
    application.add_handler(CommandHandler("archive", archive))
    application.add_handler(CommandHandler("cast", cast))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("code", code))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, received_cast))
    application.add_handler(CallbackQueryHandler(inline_button))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Установка webhook
    logger.info(f"Setting webhook to {WEBHOOK_URL}")
    import asyncio
    asyncio.run(application.bot.set_webhook(WEBHOOK_URL))
    logger.info("Webhook set successfully!")

    # Flask run (в проде — через gunicorn)
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    main()