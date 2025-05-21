from flask import Flask, request
import telegram
import os

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

@app.route('/')
def index():
    return "Бот работает"

@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    chat_id = update.message.chat.id
    message = update.message.text
    bot.send_message(chat_id=chat_id, text="Ты написал: " + message)
    return 'ok'
