import os
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
application = ApplicationBuilder().token(TOKEN).build()

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет. Связь установлена. Приём...")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Сигнал стабилен. Помех: 1.3%")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("эхо", echo))

@app.route('/')
def index():
    return "Бот активен."

@app.route('/webhook', methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"

if __name__ == "__main__":
    app.run(port=5000)