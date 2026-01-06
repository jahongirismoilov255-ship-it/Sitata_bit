
from pyrogram import Client
import telebot
import random
import os

# =====================
# BOT VA ADMIN
# =====================
TOKEN = "8142373417:AAHv2Mk3Jn7xPBFhBVtUC7hObERqimgKUqQ"
API_ID = 20811431       # Telegram API ID
API_HASH = "bf6c21eff58e7b92ffc9ef58b9c24629" # Telegram API Hash
CHANNEL_ID = "-1003631127626"  # Sizning privat kanal
ADMIN_ID = 7789281265

bot = telebot.TeleBot(TOKEN)

# Pyrogram client kanal postlarini olish uchun
app = Client("sitatabot", api_id=API_ID, api_hash=API_HASH)

# =====================
# /start
# =====================
@bot.message_handler(commands=["start"])
def start(m):
    uid = m.chat.id
    bot.send_message(uid,
        "✅ Tayyor!\n"
        "/post — sitata yozish\n"
        "/sitat — o‘qish"
    )

# =====================
# /post — kanalga yuborish
# =====================
@bot.message_handler(commands=["post"])
def post(m):
    uid = m.chat.id
    msg = bot.send_message(uid, "Sitata yozing:")
    bot.register_next_step_handler(msg, send_to_channel)

def send_to_channel(m):
    uid = m.chat.id
    nick = m.from_user.first_name
    text = m.text
    # Kanalga yuborish
    bot.send_message(CHANNEL_ID, f"{text}\n— {nick}")
    bot.send_message(uid, "✅ Sitata kanalga yuborildi!")

# =====================
# /sitat — kanal postlaridan random
# =====================
@bot.message_handler(commands=["sitat"])
def sitat(m):
    uid = m.chat.id
    with app:
        # Oxirgi 100 ta postni olish
        posts = [msg for msg in app.get_chat_history(CHANNEL_ID, limit=100)]
        if not posts:
            bot.send_message(uid, "❌ Sitata yo‘q")
            return
        q = random.choice(posts)
        # Xabardan text va author ajratish
        text_lines = q.text.split("\n—")
        text = text_lines[0]
        author = text_lines[1] if len(text_lines) > 1 else "Anonim"
        bot.send_message(uid, f"“{text}”\n— {author}")

# =====================
# ADMIN PANEL (reklama)
# =====================
@bot.message_handler(commands=["admin"])
def admin(m):
    if m.chat.id != ADMIN_ID:
        return
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📢 Reklama yuborish")
    bot.send_message(m.chat.id, "Admin panel", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "📢 Reklama yuborish" and m.chat.id == ADMIN_ID)
def ad_start(m):
    msg = bot.send_message(m.chat.id, "Reklama yuboring (har qanday format):")
    bot.register_next_step_handler(msg, send_ad)

def send_ad(m):
    bot.send_message(CHANNEL_ID, m.text)
    bot.send_message(ADMIN_ID, "✅ Reklama kanalga yuborildi")

# =====================
# BOT UPTIME
# =====================
import threading
from flask import Flask

flask_app = Flask("")

@flask_app.route("/")
def home():
    return "Bot is alive!"

threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))).start()
bot.infinity_polling()
