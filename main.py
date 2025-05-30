import os
import logging
import random
from flask import Flask, request, abort
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ContextTypes, MessageHandler, filters,
)
import asyncio

# ================== КОНФИГ ==================

BOT_TOKEN = os.getenv("BOT_TOKEN", "7834724747:AAEEojrbLDsXht_mQu6oFbYK7OGTDcr5FpI")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "https://shoroh-messenger.onrender.com")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# ================== ЛОГИ ====================

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ================== Flask ===================

app = Flask(__name__)

# ================== ВАРИАТИВНЫЕ ОТВЕТЫ ==================

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
    "cast_start": [
        "Терминал готов. Передай, что ты слышал или видел.",
        "Эфир открыт для твоего сигнала. Говори.",
        "Начни передачу. Мы сохраним её."
    ],
    "cast_end": [
        "Принято. Твоя запись вошла в эфир. Кто-то услышит.",
        "Лог сохранён. Назначен код временной метки.",
        "Передача завершена. Шорох сохранит."
    ],
    "help": [
        "Команды терминала активны. Запросы слушаются.",
        "Доступные сигналы: /log /cast /pulse /echo /code /archive /start /scan.",
        "Это не просто команды. Это ключи. Используй их с умом."
    ],
    "unknown": [
        "Команда не распознана эфиром.",
        "Неизвестный сигнал. Используй /help.",
        "RX: неизвестный ключ. Проверь частоту."
    ]
}

SECRET_CODE = "209A"  # для /code

# =============== HANDLERS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Проверка сигнала", callback_data='echo')],
        [InlineKeyboardButton("Последняя передача", callback_data='log')],
        [InlineKeyboardButton("Голосование за маршрут", callback_data='pulse')],
        [InlineKeyboardButton("Архив", callback_data='archive')],
        [InlineKeyboardButton("Справка", callback_data='help')],
    ]
    await update.message.reply_text(
        random.choice(REPLIES['start']),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['echo']))

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fake_log = "Сталкер заметил вспышку на горизонте. Координаты: X-23, Y-56."
    reply = random.choice(REPLIES['log']).replace("{лог}", fake_log)
    await update.message.reply_text(reply)

async def pulse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Вперёд", callback_data="pulse_forward"),
            InlineKeyboardButton("Остаться", callback_data="pulse_stay"),
            InlineKeyboardButton("Вернуться", callback_data="pulse_back"),
        ]
    ]
    await update.message.reply_text(
        random.choice(REPLIES['pulse']),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) >= 1 and context.args[0] == SECRET_CODE:
        await update.message.reply_text(random.choice(REPLIES['code_true']))
    else:
        await update.message.reply_text(random.choice(REPLIES['code_false']))

async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("ЛОГ #1", callback_data="archive_1")],
        [InlineKeyboardButton("ЛОГ #2", callback_data="archive_2")]
    ]
    await update.message.reply_text(
        random.choice(REPLIES['archive']),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Для /cast — диалог из 2х шагов
from telegram.ext import ConversationHandler

CAST_TEXT = range(1)

async def cast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['cast_start']))
    return CAST_TEXT

async def cast_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Можно здесь сохранять update.message.text
    await update.message.reply_text(random.choice(REPLIES['cast_end']))
    return ConversationHandler.END

async def cast_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Передача отменена.")
    return ConversationHandler.END

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("\n".join(REPLIES['help']))

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(REPLIES['unknown']))

# Inline кнопки — универсальный обработчик
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "echo":
        await query.edit_message_text(random.choice(REPLIES['echo']))
    elif data == "log":
        fake_log = "Сталкер заметил вспышку на горизонте. Координаты: X-23, Y-56."
        reply = random.choice(REPLIES['log']).replace("{лог}", fake_log)
        await query.edit_message_text(reply)
    elif data == "pulse":
        await query.edit_message_text(random.choice(REPLIES['pulse']))
    elif data == "archive":
        await query.edit_message_text(random.choice(REPLIES['archive']))
    elif data == "help":
        await query.edit_message_text("\n".join(REPLIES['help']))
    elif data.startswith("pulse_"):
        if data.endswith("forward"):
            await query.edit_message_text("Выбран маршрут: Вперёд.")
        elif data.endswith("stay"):
            await query.edit_message_text("Выбран маршрут: Остаться.")
        elif data.endswith("back"):
            await query.edit_message_text("Выбран маршрут: Вернуться.")
    elif data.startswith("archive_"):
        await query.edit_message_text(f"Открыт {data.replace('archive_', 'ЛОГ #')}. Передача в процессе...")

# ================== TELEGRAM BOT APP ==================

application = Application.builder().token(BOT_TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("echo", echo))
application.add_handler(CommandHandler("log", log))
application.add_handler(CommandHandler("pulse", pulse))
application.add_handler(CommandHandler("code", code))
application.add_handler(CommandHandler("archive", archive))
application.add_handler(CommandHandler("help", help_cmd))
application.add_handler(MessageHandler(filters.COMMAND, unknown))
application.add_handler(MessageHandler(filters.Regex(r'^/scan'), help_cmd))
application.add_handler(
    ConversationHandler(
        entry_points=[CommandHandler('cast', cast_start)],
        states={CAST_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, cast_save)]},
        fallbacks=[CommandHandler('cancel', cast_cancel)],
    )
)
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL, unknown))
application.add_handler(MessageHandler(filters.ALL,