from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Соединение установлено. Вы подключены к приёмнику RED-9B.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Связь стабильна. Помех: 1.3%. Переход возможен.")

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Последний ЛОГ: ЛОГ 03 — ...")

async def pulse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Вперёд"], ["Остаться"], ["Вернуться"]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Куда двигаться?", reply_markup=markup)

async def code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите скрытый код (например, D-209A):")

async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Архив логов: ЛОГ 01, ЛОГ 02, ЛОГ 03")

async def cast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Опишите, что вы слышали или видели:")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Подключиться к эфиру\n"
        "/echo - Проверка сигнала\n"
        "/log - Последний ЛОГ\n"
        "/pulse - Голосование\n"
        "/code - Ввод скрытого сигнала\n"
        "/archive - Архив логов\n"
        "/cast - Трансляция записи\n"
        "/help - Справка по командам"
    )

if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("echo", echo))
    application.add_handler(CommandHandler("log", log))
    application.add_handler(CommandHandler("pulse", pulse))
    application.add_handler(CommandHandler("code", code))
    application.add_handler(CommandHandler("archive", archive))
    application.add_handler(CommandHandler("cast", cast))
    application.add_handler(CommandHandler("help", help_command))
    application.run_polling()

    application.add_handler(CommandHandler("code", code))
    application.add_handler(CommandHandler("archive", archive))
    application.add_handler(CommandHandler("cast", cast))
    application.add_handler(CommandHandler("help", help_command))
    application.run_polling()
