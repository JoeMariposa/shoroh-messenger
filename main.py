import os
import random
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN') or "7834724747:AAEEojrbLDsXht_mQu6oFbYK7OGTDcr5FpI"
WEBHOOK_PATH = f"/webhook/{TELEGRAM_TOKEN}"

app = Flask(__name__)

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
        "ЛОГ принят: (пост Лога из канала). Передача завершена.",
        "Последняя активность зафиксирована. Содержимое: {лог}.",
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
    "cast_start": [
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
}

def variant(cmd, ok=True):
    if cmd == "code":
        return random.choice(REPLIES["code_ok"] if ok else REPLIES["code_fail"])
    return random.choice(REPLIES[cmd])

application = Application.builder().token(TELEGRAM_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(variant("start"))

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(variant("echo"))

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(variant("log"))

async def pulse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(variant("pulse"))

async def code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code_entered = " ".join(context.args)
    SECRET_CODE = "12345"
    if code_entered == SECRET_CODE:
        await update.message.reply_text(variant("code", ok=True))
    else:
        await update.message.reply_text(variant("code", ok=False))

async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(variant("archive"))

cast_waiting = set()
async def cast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in cast_waiting:
        cast_waiting.add(user_id)
        await update.message.reply_text(variant("cast_start"))
    else:
        cast_waiting.remove(user_id)
        await update.message.reply_text(variant("cast_done"))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(variant("help"))

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("echo", echo))
application.add_handler(CommandHandler("log", log))
application.add_handler(CommandHandler("pulse", pulse))
application.add_handler(CommandHandler("code", code))
application.add_handler(CommandHandler("archive", archive))
application.add_handler(CommandHandler("cast", cast))
application.add_handler(CommandHandler("help", help_command))

@app.route(WEBHOOK_PATH, methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.process_update(update)
    return "ok"

@app.route("/", methods=["GET"])
def index():
    return "Shoroh Messenger bot is running."

# Запускать gunicorn так: gunicorn -k uvicorn.workers.UvicornWorker main:app