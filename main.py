import os
import random
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)

# ======================================
# Варианты ответов для команд
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
CODE = os.environ.get("SECRET_CODE", "209A")  # Код можно задать как переменную среды

# ======================================
# Вспомогательная функция для выбора случайного ответа
def pick(key, extra=None):
    resp = random.choice(RESPONSES[key])
    if extra:
        resp = resp.replace("{лог}", extra)
    return resp

# ======================================
TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_HOST = os.environ.get("WEBHOOK_HOST")
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

app = Flask(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick("start"))

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick("echo"))

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Для демонстрации подставляется фраза "данные лога"
    await update.message.reply_text(pick("log", extra="данные лога"))

async def pulse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick("pulse"))

async def code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    parts = text.split(maxsplit=1)
    if len(parts) == 2 and parts[1].strip() == CODE:
        await update.message.reply_text(pick("code_true"))
    else:
        await update.message.reply_text(pick("code_false"))

async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick("archive"))

# Для команды /cast реализуем два этапа: запрос сообщения и подтверждение
USER_STATE = {}
async def cast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    USER_STATE[update.message.from_user.id] = "awaiting_cast"
    await update.message.reply_text(pick("cast_start"))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if USER_STATE.get(user_id) == "awaiting_cast":
        USER_STATE.pop(user_id)
        await update.message.reply_text(pick("cast_done"))
    else:
        # Можно тут добавить дефолтный ответ, если нужно
        pass

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick("help"))

# ======================================
def setup_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("echo", echo))
    application.add_handler(CommandHandler("log", log))
    application.add_handler(CommandHandler("pulse", pulse))
    application.add_handler(CommandHandler("code", code))
    application.add_handler(CommandHandler("archive", archive))
    application.add_handler(CommandHandler("cast", cast))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ======================================
def main():
    application = Application.builder().token(TOKEN).build()
    setup_handlers(application)
    # Настройка webhook для Flask
    @app.route("/", methods=["GET"])
    def home():
        return "OK"
    @app.route(WEBHOOK_PATH, methods=["POST"])
    async def webhook():
        await application.initialize()
        await application.process_update(Update.de_json(request.get_json(force=True), application.bot))
        return "OK"
    # Установка webhook при запуске
    async def set_webhook():
        await application.bot.delete_webhook()
        await application.bot.set_webhook(WEBHOOK_URL)
    import asyncio
    asyncio.get_event_loop().run_until_complete(set_webhook())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    main()

