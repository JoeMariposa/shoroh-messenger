import os
import random
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes
)

TOKEN = os.getenv('BOT_TOKEN', 'ваш_токен_сюда')  # Лучше использовать переменную окружения!
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"https://shoroh-messenger.onrender.com{WEBHOOK_PATH}"

app = Flask(__name__)

# Варианты для команд
replies = {
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
    "code_ok": [
        "Код принят. Активирован протокол ∆-209A. Ожидай отклика.",
        "Доступ подтверждён. Расшифровка началась.",
        "Сигнал принят. Ответ будет не для всех."
    ],
    "code_fail": [
        "Ошибка. Код отрицается эфиром.",
        "Неверная последовательность. Отказ доступа.",
        "RX: ключ не принят. Сигнал отклонён."
    ],
    "archive": [
        "Открыт архив. Передачи отсортированы. Выбери.",
        "Доступ к архиву разрешён. Некоторые записи шифруются до сих пор.",
        "Архив логов активен. Перехваченные сигналы ждут расшифровки."
    ],
    "cast_start": [
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
        "Команды терминала активны. Запросы слушаются.",
        "Доступные сигналы: /log /cast /pulse /echo /code /archive /start /scan.",
        "Это не просто команды. Это ключи. Используй их с умом."
    ]
}

# Для проверки кода — замените на свой реальный!
VALID_CODES = {"delta209a", "209a", "shoroh"}

def get_reply(key):
    return random.choice(replies[key])

# Обработчики команд
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_reply("start"))

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_reply("echo"))

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Здесь можно интегрировать реальный лог, пока выводим случайный вариант
    answer = get_reply("log").replace("{лог}", "— лог не найден —")
    await update.message.reply_text(answer)

async def pulse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_reply("pulse"))

async def code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args and context.args[0].lower() in VALID_CODES:
        await update.message.reply_text(get_reply("code_ok"))
    else:
        await update.message.reply_text(get_reply("code_fail"))

async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_reply("archive"))

# Для /cast — 2 этапа: начало и подтверждение
user_casting = set()

async def cast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_casting:
        user_casting.remove(user_id)
        await update.message.reply_text(get_reply("cast_done"))
    else:
        user_casting.add(user_id)
        await update.message.reply_text(get_reply("cast_start"))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_reply("help"))

# Инициализация приложения и регистрация команд
application = Application.builder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("echo", echo))
application.add_handler(CommandHandler("log", log))
application.add_handler(CommandHandler("pulse", pulse))
application.add_handler(CommandHandler("code", code))
application.add_handler(CommandHandler("archive", archive))
application.add_handler(CommandHandler("cast", cast))
application.add_handler(CommandHandler("help", help_command))

# Flask webhook
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"

@app.route("/", methods=["GET"])
def index():
    return "Shoroh Messenger Bot is running!"

if __name__ == "__main__":
    import asyncio
    # Установка webhook
    async def set_webhook():
        await application.bot.delete_webhook()
        await application.bot.set_webhook(WEBHOOK_URL)
        print("Webhook set:", await application.bot.get_webhook_info())
    asyncio.run(set_webhook())
    # Запуск Flask
    app.run(host="0.0.0.0", port=10000)