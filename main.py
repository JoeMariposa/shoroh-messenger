import os
import random
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)

# --- Настройки ---
TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_HOST = os.environ["WEBHOOK_HOST"]
PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

app = Flask(__name__)

# --- Вариативность ответов ---
REPLIES = {
    "start": [
        "Соединение установлено. Вы подключены к приёмнику RED-9B.",
        "Привет, сталкер. Связь стабильна. Эфир открыт.",
        "RED-9B на связи. Готов принимать сигналы.",
        "Вас слышно, приёмник активен.",
        "Эфир включён. Введите команду для продолжения работы.",
        "Передача начата. Ваш сигнал принят.",
        "Открыта связь с приёмником. Жду команд."
    ],
    "echo": [
        "Связь стабильна. Помех: 1.3%. Переход возможен.",
        "Пульсация нарушена. Предупреждение: активность слева.",
        "Эфир чист. Продолжайте приём.",
        "Получено: сигнал без искажений.",
        "Внимание: кратковременный сбой, сигнал восстановлен.",
        "Сигнал нормализован. Продолжаем работу.",
        "Волнения нет. Соединение устойчивое."
    ],
    "log": [
        "Последняя передача: {}",
        "Актуальный лог: {}",
        "Получен последний отчёт: {}",
        "Записано: {}",
        "Последний сигнал: {}",
        "Фиксирую текущий лог: {}",
        "В базе отмечен такой лог: {}"
    ],
    "pulse": [
        "Выберите направление движения.",
        "Ваша интуиция — главный ориентир. Вперёд, остаться или вернуться?",
        "Где ваша следующая точка? Проголосуйте.",
        "Куда отправимся на этот раз?",
        "Сталкер, твой выбор определит исход. Действуй.",
        "Внимание, выбери направление для группы.",
        "Ожидаю голос за дальнейшие действия."
    ],
    "code_success": [
        "Код принят. Спец-лог: Секретный сигнал RED-9B активирован.",
        "Доступ разрешён. Код принят в систему.",
        "Успешно: код принят, переход на защищённый канал.",
        "Подтверждено. Введённый код корректен.",
        "Разблокировка произведена. Открыт доступ к секретному каналу."
    ],
    "code_fail": [
        "Сбой: Неверный код.",
        "Ошибка доступа. Код не принят.",
        "Нет совпадений с архивом. Повторите попытку.",
        "Код введён неверно, попробуйте снова.",
        "Доступ запрещён. Проверьте правильность кода."
    ],
    "archive": [
        "Доступные архивные логи:\n{}",
        "Выберите архивный лог для просмотра:\n{}",
        "Перечень всех доступных логов:\n{}",
        "Выберите интересующий вас архив:\n{}",
        "Список архивных сигналов:\n{}"
    ],
    "cast_question": [
        "Что именно вы хотите передать в эфир? Опишите ситуацию.",
        "Передайте текст лога: где и что вы заметили?",
        "Ваша передача важна. Сообщите детали наблюдений.",
        "Готов принять запись — расскажите, что произошло.",
        "Фиксация событий: опишите вашу передачу.",
        "Внимание, включён режим прямого эфира. Введите сообщение.",
        "Что записать в лог? Жду вашу информацию."
    ],
    "cast_confirm": [
        "Ваша запись сохранена в эфире.",
        "Передача принята. Данные будут обработаны.",
        "Лог успешно записан в архив.",
        "Информация получена. Ожидайте дальнейших инструкций.",
        "Ваше сообщение получено и записано.",
        "Лог зарегистрирован. Благодарю за сотрудничество.",
        "Данные добавлены в общий архив."
    ],
    "cancel": [
        "Передача отменена.",
        "Операция прервана по вашему запросу.",
        "Логирование отменено. Вы можете начать заново.",
        "Команда отменена. Эфир свободен.",
        "Передача отменена. Для повторной отправки используйте /cast."
    ],
    "help": [
        (
            "/start — Подключиться к эфиру\n"
            "/echo — Проверка сигнала\n"
            "/log — Последняя передача\n"
            "/pulse — Голосование за направление\n"
            "/code <код> — Ввод скрытого сигнала\n"
            "/archive — Доступ к архивным логам\n"
            "/cast — Отправка собственного лога\n"
            "/cancel — Отменить передачу лога\n"
            "/help — Справка по командам"
        )
    ],
    "unknown": [
        "Неизвестная команда. Используйте /help.",
        "Такой команды нет в системе. Ознакомьтесь со справкой.",
        "Команда не распознана. Введите /help для списка доступных.",
        "Ошибка: неизвестная команда.",
        "Система не распознала ввод. Список команд — /help."
    ],
    "archive_log": [
        "Архивная запись — {}",
        "Детали выбранного лога: {}",
        "Содержимое архива: {}",
        "Лог выбран: {}",
        "Просмотр архива: {}"
    ],
    "vote": [
        "Голос учтён: {}",
        "Выбор зарегистрирован: {}",
        "Ваш голос принят: {}",
        "Результат записан: {}",
        "Движение определено: {}"
    ]
}

def reply(key, *args):
    phrase = random.choice(REPLIES[key])
    if args:
        return phrase.format(*args)
    return phrase

# --- Минимальное хранение логов и состояния ---
LOGS = []
ARCHIVE = []
VOTES = []
CAST_STATE = set()

# --- Telegram Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(reply("start"))

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(reply("echo"))

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if LOGS:
        await update.message.reply_text(reply("log", LOGS[-1]))
    else:
        await update.message.reply_text("Нет новых передач. Архив пуст.")

async def pulse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Пример голосования (вариант отправки inline-кнопок опционально)
    await update.message.reply_text(reply("pulse"))
    VOTES.append(update.effective_user.id)  # Примитивно: просто добавляем id голосовавших

async def code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = " ".join(context.args) if context.args else ""
    if code.strip().lower() == "d-209a":
        await update.message.reply_text(reply("code_success"))
    else:
        await update.message.reply_text(reply("code_fail"))

async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ARCHIVE:
        archive_list = "\n".join([f"{i+1}. {l}" for i, l in enumerate(ARCHIVE)])
        await update.message.reply_text(reply("archive", archive_list))
    else:
        await update.message.reply_text("Архив пуст.")

async def cast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    CAST_STATE.add(user_id)
    await update.message.reply_text(reply("cast_question"))

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in CAST_STATE:
        CAST_STATE.remove(user_id)
        await update.message.reply_text(reply("cancel"))
    else:
        await update.message.reply_text("Нет активной передачи для отмены.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(reply("help"))

async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in CAST_STATE:
        text = update.message.text.strip()
        LOGS.append(text)
        ARCHIVE.append(text)
        CAST_STATE.remove(user_id)
        await update.message.reply_text(reply("cast_confirm"))
    else:
        await update.message.reply_text(reply("unknown"))

# --- Flask webhook обработчик ---
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    from telegram import Update
    import telegram
    update = Update.de_json(request.get_json(force=True), telegram.Bot(TOKEN))
    app.bot_app.create_task(app.application.process_update(update))
    return '', 200

@app.route("/", methods=["GET", "HEAD"])
def index():
    return "STALKER RED-9B: Service active.", 200

# --- Инициализация Telegram Application ---
def main():
    import asyncio
    from telegram.ext import ApplicationBuilder

    app.application = ApplicationBuilder().token(TOKEN).build()

    app.application.add_handler(CommandHandler("start", start))
    app.application.add_handler(CommandHandler("echo", echo))
    app.application.add_handler(CommandHandler("log", log))
    app.application.add_handler(CommandHandler("pulse", pulse))
    app.application.add_handler(CommandHandler("code", code))
    app.application.add_handler(CommandHandler("archive", archive))
    app.application.add_handler(CommandHandler("cast", cast))
    app.application.add_handler(CommandHandler("cancel", cancel))
    app.application.add_handler(CommandHandler("help", help_command))
    app.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))

    app.bot_app = asyncio.get_event_loop()
    asyncio.run(app.application.initialize())
    app.application.bot.set_webhook(WEBHOOK_URL)
    print("Webhook set:", app.application.bot.get_webhook_info())

if __name__ == "__main__":
    main()
    app.run(host="0.0.0.0", port=PORT)