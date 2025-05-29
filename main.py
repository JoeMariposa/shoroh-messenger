import os
import logging
import random
from flask import Flask, request, abort
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)

TOKEN = os.getenv('BOT_TOKEN', 'YOUR_TELEGRAM_BOT_TOKEN')
WEBHOOK_PATH = f"/webhook/{TOKEN}"

# Варианты реплик для каждой команды
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
    'help': [
        "Команды терминала активны. Запросы слушаются.",
        "Доступные сигналы: /log /cast /pulse /echo /code /archive /start /scan.",
        "Это не просто команды. Это ключи. Используй их с умом."
    ],
    'cast': [
        "Терминал готов. Передай, что ты слышал или видел.",
        "Эфир открыт для твоего сигнала. Говори.",
        "Начни передачу. Мы сохраним её."
    ],
    'cast_after': [
        "Принято. Твоя запись вошла в эфир. Кто-то услышит.",
        "Лог сохранён. Назначен код временной метки.",
        "Передача завершена. Шорох сохранит."
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
    'unknown': [
        "Неизвестная команда. Используйте /help."
    ]
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# --- Хендлеры для команд ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['start']))

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['echo']))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['help']))

async def cast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['cast']))
    # Ожидаем следующий текст сообщения от пользователя
    context.user_data['waiting_cast'] = True

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting_cast'):
        await update.message.reply_text(random.choice(REPLIES['cast_after']))
        context.user_data['waiting_cast'] = False

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Здесь вместо {лог} вставьте фактическую последнюю запись, если храните где-то
    await update.message.reply_text(random.choice(REPLIES['log']).replace('{лог}', 'нет данных'))

async def pulse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['pulse']))

async def code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверка кода — условно: если передан аргумент "1234", считаем его валидным
    try:
        code_arg = context.args[0]
        if code_arg == "1234":
            await update.message.reply_text(random.choice(REPLIES['code_ok']))
        else:
            await update.message.reply_text(random.choice(REPLIES['code_fail']))
    except (IndexError, ValueError):
        await update.message.reply_text("Укажите код после /code")

async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['archive']))

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['unknown']))

# --- Регистрируем хендлеры ---
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("echo", echo))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("cast", cast))
application.add_handler(CommandHandler("log", log))
application.add_handler(CommandHandler("pulse", pulse))
application.add_handler(CommandHandler("code", code))
application.add_handler(CommandHandler("archive", archive))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))
application.add_handler(MessageHandler(filters.COMMAND, unknown))

# --- Flask Webhook ---
@app.route("/", methods=["GET"])
def index():
    return "ok", 200

@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.create_task(application.process_update(update))
        return "ok", 200
    else:
        abort(403)

if __name__ == "__main__":
    # Только запуск Flask, не запускать polling!
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))