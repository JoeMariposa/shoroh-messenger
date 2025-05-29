import os
import random
import logging

from flask import Flask, request, abort
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN"  # Укажите токен или передавайте через переменные окружения
WEBHOOK_PATH = f"/webhook/{TOKEN}"
PORT = int(os.getenv("PORT", 10000))

# ------ Вариативные реплики ------
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
        "Сектор разветвлён. Укажи направление:"
    ],
    'pulse_buttons': [
        [
            InlineKeyboardButton("Вперёд", callback_data="forward"),
            InlineKeyboardButton("Остаться", callback_data="stay"),
            InlineKeyboardButton("Вернуться", callback_data="back")
        ]
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
    'cast': [
        "Терминал готов. Передай, что ты слышал или видел.",
        "Эфир открыт для твоего сигнала. Говори.",
        "Начни передачу. Мы сохраним её."
    ],
    'cast_saved': [
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
        "Неизвестная команда. Используй /help для справки."
    ],
    'pulse_vote': [
        "Результат принят: направление – {vote}. Решение зафиксировано."
    ]
}

# ------ Логгирование ------
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

app = Flask(__name__)

application = Application.builder().token(TOKEN).build()

# Храним статус для /cast — ожидает ли пользователь ввода текста
USER_CAST_WAIT = {}

# ------ Универсальный выбор реплики ------
def pick_reply(key, **kwargs):
    template = random.choice(REPLIES[key])
    if isinstance(template, dict):
        text = template['text']
    else:
        text = template
    return text.format(**kwargs)

# ------ Командные обработчики ------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick_reply('start'))

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick_reply('echo'))

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Место для интеграции реального логирования
    await update.message.reply_text(pick_reply('log', лог='Содержимое последней передачи'))

async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick_reply('archive'))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick_reply('help'))

async def pulse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        pick_reply('pulse'),
        reply_markup=InlineKeyboardMarkup(REPLIES['pulse_buttons'])
    )

# Inline-кнопки голосования /pulse
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    vote_map = {"forward": "вперёд", "stay": "остаться", "back": "вернуться"}
    if query.data in vote_map:
        await query.answer()
        await query.edit_message_text(
            REPLIES['pulse_vote'][0].format(vote=vote_map[query.data])
        )
    else:
        await query.answer("Неизвестный выбор", show_alert=True)

# /code обработчик
async def code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code_entered = ' '.join(context.args) if context.args else ''
    correct_codes = ['209A', 'delta', 'secret']  # ваш список допустимых кодов
    if code_entered and code_entered.lower() in [x.lower() for x in correct_codes]:
        await update.message.reply_text(pick_reply('code_ok'))
    else:
        await update.message.reply_text(pick_reply('code_fail'))

# /cast: сначала отправить приглашение, потом ждать текст
async def cast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick_reply('cast'))
    USER_CAST_WAIT[update.effective_chat.id] = True

# При получении любого текста: если ждали ввод после /cast — отправить подтверждение
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if USER_CAST_WAIT.get(chat_id):
        await update.message.reply_text(pick_reply('cast_saved'))
        USER_CAST_WAIT[chat_id] = False

# Обработка неизвестных команд
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick_reply('unknown'))

# ------ Flask webhook endpoint ------
@app.route("/")
def root():
    return "Bot is running!"

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.update_queue.put_nowait(update)
        return "ok"
    else:
        abort(403)

# ------ Регистрация хендлеров ------
application.add_handler(CommandHandler('start', start))
application.add_handler(CommandHandler('echo', echo))
application.add_handler(CommandHandler('log', log))
application.add_handler(CommandHandler('pulse', pulse))
application.add_handler(CallbackQueryHandler(button_callback))
application.add_handler(CommandHandler('archive', archive))
application.add_handler(CommandHandler('help', help_command))
application.add_handler(CommandHandler('code', code))
application.add_handler(CommandHandler('cast', cast))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
application.add_handler(MessageHandler(filters.COMMAND, unknown))

# ------ Запуск ------
if __name__ == '__main__':
    import asyncio

    async def on_startup():
        # Устанавливаем webhook
        url = os.getenv("RENDER_EXTERNAL_URL")
        if url:
            webhook_url = f"{url}{WEBHOOK_PATH}"
        else:
            webhook_url = f"https://YOUR_DOMAIN_OR_RENDER_URL{WEBHOOK_PATH}"
        await application.bot.set_webhook(webhook_url)
        logging.info(f"Webhook set: {webhook_url}")

    async def main():
        await on_startup()
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        app.run(host="0.0.0.0", port=PORT)

    asyncio.run(main())