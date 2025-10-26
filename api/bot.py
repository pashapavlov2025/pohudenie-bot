from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from supabase import create_client
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta, timezone
import os, asyncio

# ─── Config ──────────────────────────────────────────────────────────────
TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
TZ = timezone(timedelta(hours=3))  # Moscow time

# ─── Commands ────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    name = update.effective_user.first_name
    existing = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
    if existing.data:
        await update.message.reply_text(f"С возвращением, {name}! 💪")
    else:
        supabase.table("users").insert({"telegram_id": telegram_id, "name": name}).execute()
        await update.message.reply_text(
            f"Привет, {name}! Я помогу тебе следить за водой, активностью и весом 💧⚖️"
        )

async def weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await update.message.reply_text(f"✅ Вес {value} кг записан!")

async def note(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# ─── Reminder logic ──────────────────────────────────────────────────────
async def send_message(bot, chat_id, text):
    try:
        await bot.send_message(chat_id=int(chat_id), text=text)
    except Exception as e:
        print(f"Ошибка отправки {chat_id}: {e}")

async def water_reminder(bot):
    users = supabase.table("users").select("telegram_id").execute()
    for u in users.data:
        await send_message(bot, u["telegram_id"], "💧 Сделай пару глотков воды и немного разминки!")

async def weight_reminder(bot):
    now = datetime.now(TZ)
    cutoff = now - timedelta(days=3)
    users = supabase.table("users").select("id, telegram_id").execute()
    for u in users.data:
        # Проверяем, когда был последний вес
        w = supabase.table("weights").select("date").eq("user_id", u["id"]).order("date", desc=True).limit(1).execute()
        if not w.data or datetime.fromisoformat(w.data[0]["date"].replace("Z", "+00:00")) < cutoff:
            await send_message(bot, u["telegram_id"], "⚖️ Пора взвеситься и записать результат!")

def schedule_jobs(app):
    scheduler = BackgroundScheduler(timezone=TZ)

    # 💧 каждые 3 часа с 8:00 до 20:00
    for h in [8, 11, 14, 17, 20]:
        scheduler.add_job(lambda: asyncio.run(water_reminder(app.bot)), "cron", hour=h, minute=0)

    # ⚖️ проверка взвешивания раз в день в 09:00
    scheduler.add_job(lambda: asyncio.run(weight_reminder(app.bot)), "cron", hour=9, minute=0)

    scheduler.start()
    print("⏰ Планировщик напоминаний активен.")

# ─── App entry ───────────────────────────────────────────────────────────
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("weight", weight))
    app.add_handler(CommandHandler("note", note))

    schedule_jobs(app)
    app.run_polling()

if __name__ == "__main__":
    main()
