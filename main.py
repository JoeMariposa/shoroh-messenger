import logging
import os
import random

from flask import Flask, request, abort
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes, MessageHandler, filters
)

TOKEN = os.getenv('BOT_TOKEN', 'ваш-токен-бота')
WEBHOOK_PATH = f"/webhook/{TOKEN}"

# ----- Словари реплик -----
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
    'cast_finish': [
        "Принято. Твоя запись вошла в эфир. Кто-то услышит.",
        "Лог сохранён. Назначен код временной метки.",
        "Передача завершена. Шорох сохранит."
    ],
    'help': [
        "Команды терминала активны. Запросы слушаются.",
        "Доступные сигналы: /log /cast /pulse /echo /code /archive /start /scan.",
        "Это не просто команды. Это ключи. Используй их с умом."
    ],
    'unknown': [
        "Неизвестная команда. Используйте /help."
    ]
}

# ----- Логирование -----
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app_flask = Flask(__name__)

application = Application.builder().token(TOKEN).build()

# -------- Хэндлеры --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['start']))

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['echo']))

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['log']))

async def pulse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['pulse']))

async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['archive']))

async def cast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['awaiting_cast'] = True
    await update.message.reply_text(random.choice(REPLIES['cast_start']))

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_cast', False):
        context.user_data['awaiting_cast'] = False
        await update.message.reply_text(random.choice(REPLIES['cast_finish']))
    else:
        await update.message.reply_text(random.choice(REPLIES['unknown']))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['help']))

# --------- Регистрация хэндлеров ----------
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("echo", echo))
application.add_handler(CommandHandler("log", log))
application.add_handler(CommandHandler("pulse", pulse))
application.add_handler(CommandHandler("archive", archive))
application.add_handler(CommandHandler("cast", cast))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message))

# -------- Webhook endpoint для Flask --------
@app_flask.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.update_queue.put_nowait(update)
        return "ok"
    else:
        abort(403)

# --- Запуск Flask ---
if __name__ == "__main__":
    import threading
    # Стартуем telegram-bot event loop отдельно
    threading.Thread(target=application.run_polling, daemon=True).start()
    app_flask.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))