
import telebot
import json
import os
import random
import re
import time

TOKEN = os.getenv("TOKEN") or "BOT_TOKEN"
ADMIN_ID = 123456789  # <-- ADMIN ID

bot = telebot.TeleBot(TOKEN)

# =====================
# JSON FUNKSIYALAR
# =====================
def load(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

users = load("users.json", {})
quotes = load("quotes.json", [])

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

    if uid in users:
        bot.send_message(uid, "✅ Siz allaqachon ro‘yxatdan o‘tgansiz")
        return

    users[uid] = {"step": "nick"}
    save("users.json", users)
    bot.send_message(uid, "Nik yozing:")

# =====================
# NIK
# =====================
@bot.message_handler(func=lambda m: str(m.chat.id) in users and users[str(m.chat.id)]["step"] == "nick")
def set_nick(m):
    uid = str(m.chat.id)
    nick = m.text.strip()

    users[uid] = {
        "nick": nick
    }
    save("users.json", users)

    bot.send_message(uid,
        f"✅ Tayyor!\n"
        f"/post — sitata yozish\n"
        f"/sitat — o‘qish\n"
        f"/myquotes — o‘chirish"
    )

# =====================
# POST
# =====================
@bot.message_handler(commands=["post"])
def post(m):
    uid = str(m.chat.id)
    if uid not in users:
        bot.send_message(uid, "/start bosing")
        return

    msg = bot.send_message(uid, "Sitata yozing:")
    bot.register_next_step_handler(msg, save_quote)

def save_quote(m):
    text = m.text.strip()
    uid = str(m.chat.id)

    if has_ad(text):
        bot.send_message(uid, "🚫 Reklama mumkin emas")
        return

    quotes.append({
        "id": uid,
        "author": users[uid]["nick"],
        "text": text
    })
    save("quotes.json", quotes)
    bot.send_message(uid, "✅ Saqlandi")

# =====================
# /sitat
# =====================
@bot.message_handler(commands=["sitat"])
def sitat(m):
    if not quotes:
        bot.send_message(m.chat.id, "❌ Yo‘q")
        return

    q = random.choice(quotes)
    bot.send_message(m.chat.id, f"“{q['text']}”\n— {q['author']}")

# =====================
# O‘Z SITATALARINI O‘CHIRISH
# =====================
@bot.message_handler(commands=["myquotes"])
def my_quotes(m):
    uid = str(m.chat.id)
    my = [q for q in quotes if q["id"] == uid]

    if not my:
        bot.send_message(uid, "❌ Sizda yo‘q")
        return

    text = "🗑 O‘chirish uchun raqam yozing:\n\n"
    for i, q in enumerate(my):
        text += f"{i+1}. {q['text']}\n"

    msg = bot.send_message(uid, text)
    bot.register_next_step_handler(msg, delete_quote, my)

def delete_quote(m, my):
    try:
        i = int(m.text) - 1
        q = my[i]
        quotes.remove(q)
        save("quotes.json", quotes)
        bot.send_message(m.chat.id, "✅ O‘chirildi")
    except:
        bot.send_message(m.chat.id, "❌ Xato")

# =====================
# ADMIN PANEL
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
    msg = bot.send_message(m.chat.id, "Reklama yuboring (text / rasm / video / audio / link):")
    bot.register_next_step_handler(msg, send_ad)

def send_ad(m):
    sent = 0
    for uid in users:
        try:
            bot.copy_message(
                chat_id=uid,
                from_chat_id=m.chat.id,
                message_id=m.message_id
            )
            sent += 1
        except:
            pass

    bot.send_message(m.chat.id, f"✅ {sent} ta foydalanuvchiga yuborildi")

# =====================
# START
# =====================
print("Sitatabot v1.2 ishga tushdi")

while True:
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print("Xato:", e)
        time.sleep(5)
