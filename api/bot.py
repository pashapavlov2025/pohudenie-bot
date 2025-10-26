from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from supabase import create_client
import os

# ─── Environment ────────────────────────────────────────────────────────────────
TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ─── Commands ───────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Register new user or greet existing."""
    telegram_id = str(update.effective_user.id)
    name = update.effective_user.first_name

    # Check if user exists
    existing = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
    if existing.data:
        await update.message.reply_text(f"С возвращением, {name}! 💪")
    else:
        supabase.table("users").insert({"telegram_id": telegram_id, "name": name}).execute()
        await update.message.reply_text(
            f"Привет, {name}! Я помогу тебе отслеживать вес и привычки. "
            "Используй /weight или /note, чтобы начать 📊"
        )

async def weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store weight entry."""
    if not context.args:
        await update.message.reply_text("Напиши вес, например: /weight 94.8")
        return

    telegram_id = str(update.effective_user.id)
    user = supabase.table("users").select("id").eq("telegram_id", telegram_id).single().execute()
    if not user.data:
        await update.message.reply_text("Сначала введи /start, чтобы зарегистрироваться.")
        return

    value = float(context.args[0])
    supabase.table("weights").insert({"user_id": user.data["id"], "weight": value}).execute()
    await update.message.reply_text(f"✅ Вес {value} кг записан! Продолжаем движение к цели!")

async def note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store daily note."""
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Напиши заметку, например: /note ел рыбу и салат 🐟🥗")
        return

    telegram_id = str(update.effective_user.id)
    user = supabase.table("users").select("id").eq("telegram_id", telegram_id).single().execute()
    if not user.data:
        await update.message.reply_text("Сначала введи /start, чтобы зарегистрироваться.")
        return

    supabase.table("notes").insert({
        "user_id": user.data["id"],
        "text": text,
        "category": "general"
    }).execute()

    await update.message.reply_text(f"📝 Запомнил: «{text}»")

# ─── Application ────────────────────────────────────────────────────────────────
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("weight", weight))
    app.add_handler(CommandHandler("note", note))
    app.run_polling()

if __name__ == "__main__":
    main()
