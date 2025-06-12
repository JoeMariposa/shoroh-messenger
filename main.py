import os
import random
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
)
import asyncio

# --- Атмосферные варианты команд ---
ECHO_ALIASES = {"echo", "проверка", "test", "эхо", "check"}
START_ALIASES = {"start", "контакт", "старт"}
LOG_ALIASES = {"log", "лог", "трафик"}
PULSE_ALIASES = {"pulse", "маршрут", "выбор"}
CODE_ALIASES = {"code", "код", "ключ"}
ARCHIVE_ALIASES = {"archive", "архив", "старое"}
CAST_ALIASES = {"cast", "передать", "сигнал"}
HELP_ALIASES = {"help", "помощь", "справка"}
SCAN_ALIASES = {"scan", "скан", "искать"}

ADMIN_IDS = {642787882}
LOG_HISTORY = []
ARCHIVE_PAGE_SIZE = 5

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

START_REPLY_OPTIONS = [["/help", "/echo"], ["/log", "/cast"]]
CODE = os.environ.get("SECRET_CODE", "209A")
USER_STATE = {}

def pick(key, extra=None):
    resp = random.choice(RESPONSES[key])
    if extra:
        resp = resp.replace("{лог}", extra)
    return resp

# Команды с /
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup(START_REPLY_OPTIONS, resize_keyboard=True)
    await update.message.reply_text(pick("start"), reply_markup=reply_markup)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick("echo"))

async def code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = update.message.text.split(maxsplit=1)
    if len(parts) == 2 and parts[1].strip().upper() == CODE:
        await update.message.reply_text(pick("code_true"))
    else:
        await update.message.reply_text(pick("code_false"))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Команды терминала:\n"
        "📡 /start — подключиться к эфиру\n"
        "🔊 /echo — проверить сигнал\n"
        "🗒 /log — последняя передача\n"
        "🔻 /pulse — выбрать маршрут\n"
        "🔑 /code <код> — ввести скрытый сигнал\n"
        "🗄 /archive — архив логов\n"
        "✉️ /cast — отправить запись\n"
        "🆘 /help — справка\n"
        "— Используй атмосферные слова, терминал поймёт…"
    )

# Остальные обработчики (аналогично вашему коду)
async def send_pulse_keyboard(update, context):
    keyboard = [
        [
            InlineKeyboardButton("Вперёд", callback_data='pulse_forward'),
            InlineKeyboardButton("Остаться", callback_data='pulse_stay'),
            InlineKeyboardButton("Вернуться", callback_data='pulse_back')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(pick("pulse"), reply_markup=reply_markup)

async def publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("У вас нет прав для публикации лога.")
        return
    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("Используйте: /publish <текст лога>")
        return
    log_text = parts[1]
    LOG_HISTORY.append(log_text)
    await update.message.reply_text("Лог опубликован.")

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if LOG_HISTORY:
        last_log = LOG_HISTORY[-1]
        await update.message.reply_text(f"ЛОГ# {len(LOG_HISTORY)}\n{last_log}")
    else:
        await update.message.reply_text("Логов пока нет.")

async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_archive_page(update, context, page=0)

async def send_archive_page(update_or_query, context, page=0):
    total = len(LOG_HISTORY)
    if total == 0:
        if hasattr(update_or_query, "message") and update_or_query.message:
            await update_or_query.message.reply_text("В архиве нет логов.")
        else:
            await update_or_query.edit_message_text("В архиве нет логов.")
        return
    max_page = (total - 1) // ARCHIVE_PAGE_SIZE
    start = page * ARCHIVE_PAGE_SIZE
    end = min(start + ARCHIVE_PAGE_SIZE, total)
    keyboard = []
    for i in range(start, end):
        button = InlineKeyboardButton(f"ЛОГ#{i+1}", callback_data=f"archive_log_{i}")
        keyboard.append([button])
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"archive_page_{page-1}"))
    if page < max_page:
        nav_buttons.append(InlineKeyboardButton("Дальше ➡️", callback_data=f"archive_page_{page+1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"Архив логов. Стр. {page+1} из {max_page+1}. Выберите запись:"
    if hasattr(update_or_query, "message") and update_or_query.message:
        await update_or_query.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update_or_query.edit_message_text(text, reply_markup=reply_markup)

async def archive_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("archive_log_"):
        idx = int(data.split("_")[-1])
        if 0 <= idx < len(LOG_HISTORY):
            log_text = LOG_HISTORY[idx]
            await query.edit_message_text(f"ЛОГ#{idx+1}\n{log_text}")
        else:
            await query.edit_message_text("Запись не найдена.")
    elif data.startswith("archive_page_"):
        page = int(data.split("_")[-1])
        await send_archive_page(query, context, page)

async def pulse_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice_map = {
        'pulse_forward': "Маршрут: Вперёд. Мнение учтено и отправлено на частоту.",
        'pulse_stay': "Маршрут: Остаться. Решение зафиксировано.",
        'pulse_back': "Маршрут: Вернуться. Сигнал принят."
    }
    response = choice_map.get(query.data, "Выбор не опознан.")
    await query.edit_message_text(response)

async def cast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    USER_STATE[user_id] = "awaiting_cast"
    await update.message.reply_text(pick("cast_start"))

async def handle_cast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if USER_STATE.get(user_id) == "awaiting_cast":
        USER_STATE.pop(user_id)
        log_text = update.message.text
        for admin_id in ADMIN_IDS:
            try:
                sender = update.message.from_user.username or user_id
                await context.bot.send_message(
                    admin_id,
                    f"📥 Новый пользовательский ЛОГ от @{sender}:\n{log_text}"
                )
            except Exception as e:
                print(f"Ошибка отправки админу: {e}")
        await update.message.reply_text(pick("cast_done"))
        return True
    return False

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    user_id = update.message.from_user.id
    if await handle_cast_message(update, context):
        return
    if text in START_ALIASES:
        reply_markup = ReplyKeyboardMarkup(START_REPLY_OPTIONS, resize_keyboard=True)
        await update.message.reply_text(pick("start"), reply_markup=reply_markup)
    elif text in ECHO_ALIASES:
        await update.message.reply_text(pick("echo"))
    elif text in LOG_ALIASES:
        await log(update, context)
    elif text in PULSE_ALIASES:
        await send_pulse_keyboard(update, context)
    elif text.startswith("код") or text.startswith("key") or text.startswith("code") or text.startswith("/code"):
        parts = text.split(maxsplit=1)
        if len(parts) == 2 and parts[1].strip().upper() == CODE:
            await update.message.reply_text(pick("code_true"))
        else:
            await update.message.reply_text(pick("code_false"))
    elif text in ARCHIVE_ALIASES:
        await archive(update, context)
    elif text in CAST_ALIASES:
        USER_STATE[user_id] = "awaiting_cast"
        await update.message.reply_text(pick("cast_start"))
    elif text in HELP_ALIASES:
        await help_command(update, context)
    elif text in SCAN_ALIASES:
        await update.message.reply_text("Сканирование частоты... Функция будет доступна позже.")
    else:
        pass

def setup_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("echo", echo))
    application.add_handler(CommandHandler("code", code))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("publish", publish))
    application.add_handler(CommandHandler("log", log))
    application.add_handler(CommandHandler("archive", archive))
    application.add_handler(CommandHandler("cast", cast))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(pulse_button, pattern="^pulse_"))
    application.add_handler(CallbackQueryHandler(archive_button, pattern="^archive_"))

TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_HOST = os.environ.get("WEBHOOK_HOST")
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

app = Flask(__name__)

application = Application.builder().token(TOKEN).build()
setup_handlers(application)

@app.route("/", methods=["GET"])
def home():
    return "OK"

@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(application.initialize())
    loop.run_until_complete(application.process_update(update))
    loop.close()
    return "OK"

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(application.bot.delete_webhook())
    loop.run_until_complete(application.bot.set_webhook(WEBHOOK_URL))
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    main()