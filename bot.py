import os
import logging
import anthropic
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
GROUP_ID = os.environ.get("GROUP_ID", "@paxta1380")
ADMIN_IDS = os.environ.get("ADMIN_IDS", "").split(",")

claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

SYSTEM_PROMPT = """Sen ToyPaxta korxonasi uchun kontent yozuvchi yordamchisan. Namangan shahrida joylashgan, sifatli toypaxta ishlab chiqaruvchi korxona. Doim o'zbek tilida, samimiy, insonday, haqiqiy uslubda yoz. Reklama emas, do'stona muloqot kabi. Qisqa va jo'yali 3-5 jumla. Oxirida buyurtma uchun chaqiruv. 3-5 ta mos hashtag qo'sh. Emoji lar bilan jonli qil. Mahsulot: toypaxta. Faqat post matnini yoz, boshqa izoh yozma."""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Siz admin emassiz.")
        return
    await update.message.reply_text("Salom! Men ToyPaxta kontent botiman.\n\nSurat yuboring, men post yozaman.\nTasdiqlang, Telegram gruppaga joylashadi.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Siz admin emassiz.")
        return
    await update.message.reply_text("Post yozilmoqda...")
    caption = update.message.caption or "Toypaxta mahsuloti"
    try:
        message = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Bu surat haqida post yoz. Ma'lumot: {caption}"}]
        )
        post_text = message.content[0].text
        context.user_data["pending_post"] = post_text
        context.user_data["pending_photo"] = update.message.photo[-1].file_id
        await update.message.reply_text(f"Post tayyor:\n\n{post_text}\n\n/tasdiqlash - Gruppaga joylash\n/qayta - Boshqacha yoz\n/bekor - Bekor qilish")
    except Exception as e:
        logger.error(f"Xato: {e}")
        await update.message.reply_text("Xatolik yuz berdi. Qaytadan urinib koring.")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        return
    await update.message.reply_text("Post yozilmoqda...")
    caption = update.message.caption or "Toypaxta mahsuloti"
    try:
        message = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Video uchun post yoz. Mavzu: {caption}"}]
        )
        post_text = message.content[0].text
        context.user_data["pending_post"] = post_text
        context.user_data["pending_video"] = update.message.video.file_id
        await update.message.reply_text(f"Post tayyor:\n\n{post_text}\n\n/tasdiqlash - Gruppaga joylash\n/qayta - Boshqacha yoz\n/bekor - Bekor qilish")
    except Exception as e:
        await update.message.reply_text("Xatolik yuz berdi.")

async def tasdiqlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        return
    post_text = context.user_data.get("pending_post")
    photo_id = context.user_data.get("pending_photo")
    video_id = context.user_data.get("pending_video")
    if not post_text:
        await update.message.reply_text("Joylash uchun hech narsa yoq.")
        return
    try:
        if photo_id:
            await context.bot.send_photo(chat_id=GROUP_ID, photo=photo_id, caption=post_text)
        elif video_id:
            await context.bot.send_video(chat_id=GROUP_ID, video=video_id, caption=post_text)
        else:
            await context.bot.send_message(chat_id=GROUP_ID, text=post_text)
        context.user_data.clear()
        await update.message.reply_text("Post muvaffaqiyatli joylandi!")
    except Exception as e:
        await update.message.reply_text(f"Xatolik: {e}")

async def qayta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        return
    await update.message.reply_text("Yangi post yozilmoqda...")
    try:
        message = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": "Boshqacha uslubda yangi post yoz. Toypaxta mahsuloti haqida."}]
        )
        new_post = message.content[0].text
        context.user_data["pending_post"] = new_post
        await update.message.reply_text(f"Yangi post:\n\n{new_post}\n\n/tasdiqlash - Gruppaga joylash\n/qayta - Yana boshqacha\n/bekor - Bekor qilish")
    except Exception as e:
        await update.message.reply_text("Xatolik yuz berdi.")

async def bekor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        return
    context.user_data.clear()
    await update.message.reply_text("Bekor qilindi.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tasdiqlash", tasdiqlash))
    app.add_handler(CommandHandler("qayta", qayta))
    app.add_handler(CommandHandler("bekor", bekor))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    logger.info("Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
