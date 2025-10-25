# api/bot.py
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from http.server import BaseHTTPRequestHandler

TOKEN = os.getenv("BOT_TOKEN")

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет, я твой ироничный партнёр по похудению 😎 "
        "Пиши /weight или /note — начнём!"
    )

async def weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Напиши вес, например: /weight 94.8")
        return
    weight = context.args[0]
    await update.message.reply_text(f"Принято: {weight} кг. "
                                    "Главное, не взвешивайся после пиццы 🍕")

async def note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Напиши, что ел или чем занимался 💪")
        return
    await update.message.reply_text(f"Запомнил: “{text}”. Звучит неплохо!")

# HTTP endpoint for Vercel
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive on Render!")

# Telegram bot setup
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("weight", weight))
    app.add_handler(CommandHandler("note", note))
    app.run_polling()
