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
    bot.send_message(chat_id=chat_id, text="Вы сказали: " + message)
    return 'ok'

if __name__ == '__main__':
    PORT = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=PORT)
