from flask import Flask, request
from telegram import Bot, Update, ReplyKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters

TOKEN = "7834724747:AAEEojrbLDsXht_mQu6oFbYK7OGTDcr5FpI"
bot = Bot(token=TOKEN)
app = Flask(__name__)

@app.route('/')
def index():
    return "ShorohMessenger is active"

@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

def start(update, context):
    update.message.reply_text("Соединение установлено. Вы подключены к приёмнику RED-9B.")

def echo(update, context):
    update.message.reply_text("Связь стабильна. Помех: 1.3%. Переход возможен.")

def log(update, context):
    update.message.reply_text("ЛОГ 03: Неопознанная активность за границей сектора...")

def help_command(update, context):
    update.message.reply_text("/вход — Подключиться к эфиру\n/эхо — Проверка сигнала\n/лог — Последний ЛОГ\n/помощь — Справка по командам")

dispatcher = Dispatcher(bot, None, workers=0)
dispatcher.add_handler(CommandHandler("вход", start))
dispatcher.add_handler(CommandHandler("эхо", echo))
dispatcher.add_handler(CommandHandler("лог", log))
dispatcher.add_handler(CommandHandler("помощь", help_command))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
