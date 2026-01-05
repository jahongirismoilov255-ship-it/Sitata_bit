import telebot
import re
import random
import time
import json
import os
from flask import Flask
from threading import Thread

TOKEN = "8142373417:AAHTyYVH2tD0QzFclF44jLZjdz-vEEHbtvo"
bot = telebot.TeleBot(TOKEN)

# =======================
# JSON YUKLASH / SAQLASH
# =======================

def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

users = load_json("users.json", {})
nicks = set(load_json("nicks.json", []))
quotes = load_json("quotes.json", [])

# =======================
# REKLAMA ANIQLASH
# =======================

link_pattern = re.compile(
    r"(https?://|www\.|t\.me/|\.com|\.ru|\.tj|\.uz)",
    re.IGNORECASE
)

def has_ad(text):
    return bool(link_pattern.search(text))

# =======================
# /start
# =======================

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    users[user_id] = {"step": "lang"}
    save_json("users.json", users)

    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🇺🇿 O‘zbek", "🇹🇯 Тоҷикӣ", "🇷🇺 Русский")

    bot.send_message(user_id, "Tilni tanlang:", reply_markup=kb)

# =======================
# TIL TANLASH
# =======================

@bot.message_handler(func=lambda m: str(m.chat.id) in users and users[str(m.chat.id)]["step"] == "lang")
def set_lang(message):
    user_id = str(message.chat.id)
    text = message.text

    if "O‘zbek" in text:
        lang = "uz"
    elif "Тоҷикӣ" in text:
        lang = "tj"
    elif "Русский" in text:
        lang = "ru"
    else:
        return

    users[user_id]["lang"] = lang
    users[user_id]["step"] = "nick"
    save_json("users.json", users)

    bot.send_message(user_id, "Nik tanlang:", reply_markup=telebot.types.ReplyKeyboardRemove())

# =======================
# NIK TANLASH
# =======================

@bot.message_handler(func=lambda m: str(m.chat.id) in users and users[str(m.chat.id)]["step"] == "nick")
def set_nick(message):
    user_id = str(message.chat.id)
    nick = message.text.strip()

    if nick in nicks:
        bot.send_message(user_id, "❌ Bu nik band")
        return

    nicks.add(nick)
    users[user_id]["nick"] = nick
    users[user_id]["step"] = "done"

    save_json("users.json", users)
    save_json("nicks.json", list(nicks))

    bot.send_message(
        user_id,
        f"✅ Tayyor!\nNikingiz: {nick}\n\n/post — sitata\n/sitat — o‘qish"
    )

# =======================
# POST
# =======================

@bot.message_handler(commands=['post'])
def post_quote(message):
    user_id = str(message.chat.id)

    if user_id not in users or users[user_id]["step"] != "done":
        bot.send_message(user_id, "❌ /start bosing")
        return

    msg = bot.send_message(user_id, "Sitata yozing:")
    bot.register_next_step_handler(msg, save_quote)

def save_quote(message):
    user_id = str(message.chat.id)
    text = message.text.strip()

    if has_ad(text):
        bot.send_message(user_id, "🚫 Reklama taqiqlangan")
        return

    quotes.append({
        "text": text,
        "lang": users[user_id]["lang"],
        "author": users[user_id]["nick"]
    })

    save_json("quotes.json", quotes)
    bot.send_message(user_id, "✅ Saqlandi")

# =======================
# /sitat
# =======================

@bot.message_handler(commands=['sitat'])
def get_quote(message):
    user_id = str(message.chat.id)

    if user_id not in users:
        bot.send_message(user_id, "❌ /start")
        return

    lang = users[user_id]["lang"]
    filtered = [q for q in quotes if q["lang"] == lang]

    if not filtered:
        bot.send_message(user_id, "❌ Sitata yo‘q")
        return

    q = random.choice(filtered)
    bot.send_message(user_id, f"“{q['text']}”\n\n— {q['author']}")

# =======================
# UPTIMEROBOT UCHUN SERVER
# =======================

app = Flask("")

@app.route("/")
def home():
    return "Bot is alive!"

def run_web():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run_web).start()

# =======================
# BOT START
# =======================

print("Bot ishga tushdi...")
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print("Xatolik:", e)
        time.sleep(5)
