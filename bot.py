import telebot
import random
import os
from flask import Flask
import threading

TOKEN = "TOKENING"
CHANNEL_ID = -1003631127626
ADMIN_ID = 7789281265

bot = telebot.TeleBot(TOKEN)

# =====================
# /start
# =====================
@bot.message_handler(commands=["start"])
def start(m):
    bot.send_message(
        m.chat.id,
        "✅ Tayyor!\n"
        "/post — sitata yozish\n"
        "/sitat — o‘qish"
    )

# =====================
# /post
# =====================
@bot.message_handler(commands=["post"])
def post(m):
    msg = bot.send_message(m.chat.id, "Sitata yozing:")
    bot.register_next_step_handler(msg, send_to_channel)

def send_to_channel(m):
    nick = m.from_user.first_name
    bot.send_message(CHANNEL_ID, f"{m.text}\n— {nick}")
    bot.send_message(m.chat.id, "✅ Kanalga yuborildi!")

# =====================
# /sitat (random)
# =====================
@bot.message_handler(commands=["sitat"])
def sitat(m):
    updates = bot.get_updates(limit=100)
    quotes = []

    for u in updates:
        if u.channel_post and u.channel_post.chat.id == CHANNEL_ID:
            if u.channel_post.text:
                quotes.append(u.channel_post.text)

    if not quotes:
        bot.send_message(m.chat.id, "❌ Hozircha sitata yo‘q")
        return

    bot.send_message(m.chat.id, random.choice(quotes))

# =====================
# ADMIN
# =====================
@bot.message_handler(commands=["admin"])
def admin(m):
    if m.chat.id != ADMIN_ID:
        return
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📢 Reklama yuborish")
    bot.send_message(m.chat.id, "Admin panel", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "📢 Reklama yuborish" and m.chat.id == ADMIN_ID)
def ad(m):
    msg = bot.send_message(m.chat.id, "Reklamani yuboring:")
    bot.register_next_step_handler(msg, send_ad)

def send_ad(m):
    bot.send_message(CHANNEL_ID, m.text)
    bot.send_message(ADMIN_ID, "✅ Yuborildi")

# =====================
# UPTIME
# =====================
app = Flask("")

@app.route("/")
def home():
    return "Bot alive"

threading.Thread(
    target=lambda: app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
).start()

bot.infinity_polling()
