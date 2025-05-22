from flask import Flask, request
import telegram
import os
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in environment variables")

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

# Логи и пользовательские сообщения
LOGS = {
    "LOG 01": "Transmission: Signal detected at 0300 hours.",
    "LOG 02": "Anomaly reported in sector 7.",
    "LOG 03": "Last contact with unit RED-9B at 1800."
}
USER_STATE = {}        # chat_id: "awaiting_log" или None
USER_SUBMISSIONS = {}  # chat_id: [user_logs]

# Логирование ошибок (отправляет в консоль)
logging.basicConfig(level=logging.INFO)

@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
    try:
        update = telegram.Update.de_json(request.get_json(force=True), bot)

        # Обработка callback-кнопок
        if update.callback_query:
            chat_id = update.callback_query.message.chat.id
            query = update.callback_query
            query.answer()
            data = query.data
            if data.startswith("vote_"):
                vote = data.split("_")[1].capitalize()
                bot.send_message(chat_id=chat_id, text=f"Голос учтён: {vote}")
            elif data in LOGS:
                bot.send_message(chat_id=chat_id, text=f"{data}: {LOGS[data]}")
            return "ok"

        # Обработка команд
        if update and update.message and update.message.text:
            chat_id = update.message.chat.id
            text = update.message.text.strip()

            # 1. State: Ждём лог после /частота
            if USER_STATE.get(chat_id) == "awaiting_log":
                USER_SUBMISSIONS.setdefault(chat_id, []).append(text)
                bot.send_message(chat_id=chat_id, text="Ваша запись сохранена в эфире.")
                USER_STATE[chat_id] = None
                return "ok"

            lower = text.lower()
            if lower.startswith("/вход"):
                bot.send_message(chat_id=chat_id, text="Соединение установлено. Вы подключены к приёмнику RED-9B.")

            elif lower.startswith("/эхо"):
                if random.random() < 0.8:
                    bot.send_message(chat_id=chat_id, text="Связь стабильна. Помех: 1.3%. Переход возможен.")
                else:
                    bot.send_message(chat_id=chat_id, text="Пульсация нарушена. Предупреждение: активность слева.")

            elif lower.startswith("/лог"):
                latest_log = LOGS.get("LOG 03", "Нет доступных логов.")
                bot.send_message(chat_id=chat_id, text=f"Последняя передача: {latest_log}")

            elif lower.startswith("/пульс"):
                keyboard = [[
                    InlineKeyboardButton("Вперед", callback_data="vote_forward"),
                    InlineKeyboardButton("Остаться", callback_data="vote_stay"),
                    InlineKeyboardButton("Вернуться", callback_data="vote_back")
                ]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                bot.send_message(
                    chat_id=chat_id,
                    text="Визуальный выбор: Куда пойдёт сталкер?",
                    reply_markup=reply_markup
                )

            elif lower.startswith("/код"):
                code = text[5:].strip()
                if code == "D-209A":
                    bot.send_message(chat_id=chat_id, text="Код принят. Спец-лог: Секретный сигнал RED-9B активирован.")
                else:
                    bot.send_message(chat_id=chat_id, text="Сбой: Неверный код.")

            elif lower.startswith("/архив"):
                keyboard = [[InlineKeyboardButton(log, callback_data=log)] for log in LOGS.keys()]
                reply_markup = InlineKeyboardMarkup(keyboard)
                bot.send_message(chat_id=chat_id, text="Доступные архивные логи:", reply_markup=reply_markup)

            elif lower.startswith("/частота"):
                USER_STATE[chat_id] = "awaiting_log"
                bot.send_message(
                    chat_id=chat_id,
                    text="Хотите передать свою запись в эфир? Опишите, что вы видели или слышали."
                )

            elif lower.startswith("/помощь"):
                help_text = (
                    "/вход — Подключиться к эфиру\n"
                    "/эхо — Проверка сигнала\n"
                    "/лог — Последняя передача\n"
                    "/пульс — Голосование за направление\n"
                    "/код — Ввод скрытого сигнала\n"
                    "/архив — Доступ к архивным логам\n"
                    "/частота — Отправка собственного лога\n"
                    "/помощь — Справка по командам"
                )
                bot.send_message(chat_id=chat_id, text=help_text)

        return "ok"

    except Exception as e:
        logging.exception(f"Error in webhook: {e}")
        return "ok"

@app.route("/", methods=["GET"])
def index():
    return "Bot is running."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))



