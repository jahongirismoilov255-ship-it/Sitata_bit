
import telebot
import random
import re
import time
from pymongo import MongoClient
from flask import Flask
from threading import Thread
import os

# =====================
# BOT VA ADMIN
# =====================
TOKEN = '8142373417:AAHv2Mk3Jn7xPBFhBVtUC7hObERqimgKUqQ'
ADMIN_ID = 7789281265

bot = telebot.TeleBot(TOKEN)

# =====================
# MONGODB ULANISH
# ====================
MONGO_URI = "mongodb://jahonoke110099_db_user:ycICftHiFRr28Omw@cluster0-shard-00-00.abcde.mongodb.net:27017,cluster0-shard-00-01.abcde.mongodb.net:27017,cluster0-shard-00-02.abcde.mongodb.net:27017/sitatabot_db?ssl=true&replicaSet=atlas-xxxxx-shard-0&authSource=admin&retryWrites=true&w=majority"
client = MongoClient(MONGO_URI) 
db = client["sitatabot_db"]
users_col = db["users"]
quotes_col = db["quotes"]

# =====================
# REKLAMA ANIQLASH
# =====================
link_pattern = re.compile(r"(https?://|www\.|t\.me/)", re.I)
def has_ad(text):
    return bool(link_pattern.search(text))

# =====================
# /start (1 MARTA)
# =====================
@bot.message_handler(commands=["start"])
def start(m):
    uid = str(m.chat.id)
    if users_col.find_one({"id": uid}):
        bot.send_message(uid, "✅ Siz allaqachon ro‘yxatdan o‘tgansiz")
        return
    msg = bot.send_message(uid, "Nik yozing:")
    bot.register_next_step_handler(msg, set_nick)

def set_nick(m):
    uid = str(m.chat.id)
    nick = m.text.strip()
    users_col.insert_one({"id": uid, "nick": nick})
    bot.send_message(uid,
        "✅ Tayyor!\n"
        "/post — sitata yozish\n"
        "/sitat — o‘qish\n"
        "/myquotes — o‘chirish"
    )

# =====================
# POST
# =====================
@bot.message_handler(commands=["post"])
def post(m):
    uid = str(m.chat.id)
    user = users_col.find_one({"id": uid})
    if not user:
        bot.send_message(uid, "/start bosing")
        return
    msg = bot.send_message(uid, "Sitata yozing:")
    bot.register_next_step_handler(msg, save_quote, user["nick"])

def save_quote(m, nick):
    uid = str(m.chat.id)
    text = m.text.strip()
    if has_ad(text):
        bot.send_message(uid, "🚫 Reklama mumkin emas")
        return
    quotes_col.insert_one({"user_id": uid, "author": nick, "text": text})
    bot.send_message(uid, "✅ Saqlandi")

# =====================
# /sitat
# =====================
@bot.message_handler(commands=["sitat"])
def sitat(m):
    q = list(quotes_col.aggregate([{"$sample": {"size": 1}}]))
    if not q:
        bot.send_message(m.chat.id, "❌ Sitata yo‘q")
        return
    q = q[0]
    bot.send_message(m.chat.id, f"“{q['text']}”\n— {q['author']}")

# =====================
# O‘Z SITATALARINI O‘CHIRISH
# =====================
@bot.message_handler(commands=["myquotes"])
def myquotes(m):
    uid = str(m.chat.id)
    my_quotes = list(quotes_col.find({"user_id": uid}))
    if not my_quotes:
        bot.send_message(uid, "❌ Sizda sitata yo‘q")
        return
    txt = "🗑 O‘chirish uchun raqam yozing:\n\n"
    for i, q in enumerate(my_quotes):
        txt += f"{i+1}. {q['text']}\n"
    msg = bot.send_message(uid, txt)
    bot.register_next_step_handler(msg, delete_quote, my_quotes)

def delete_quote(m, my_quotes):
    try:
        i = int(m.text) - 1
        q = my_quotes[i]
        quotes_col.delete_one({"_id": q["_id"]})
        bot.send_message(m.chat.id, "✅ O‘chirildi")
    except:
        bot.send_message(m.chat.id, "❌ Xato")

# =====================
# ADMIN PANEL (REKLAMA)
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
    users = users_col.find({})
    sent = 0
    for u in users:
        try:
            bot.copy_message(u["id"], m.chat.id, m.message_id)
            sent += 1
        except:
            pass
    bot.send_message(ADMIN_ID, f"✅ {sent} ta foydalanuvchiga yuborildi")

# =====================
# FLASK UPTIME ROBOT
# =====================
app = Flask("")

@app.route("/")
def home():
    return "Bot is alive!"

def run():
    bot.infinity_polling()

Thread(target=run).start()
Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))).start()

print("Sitatabot MongoDB bilan ishga tushdi")
