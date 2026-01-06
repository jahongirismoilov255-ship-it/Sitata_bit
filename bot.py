
import telebot
import sqlite3
import os
import random
import re
import time

TOKEN = os.getenv("TOKEN") or "BOT_TOKEN"
ADMIN_ID =  7789281265 # <-- ADMIN 

DB_PATH = "/data/sitatabot.db"

bot = telebot.TeleBot(TOKEN)

# =====================
# SQLITE ULANISH
# =====================
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()

# =====================
# JADVALLAR
# =====================
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    nick TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS quotes (
    qid INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    author TEXT,
    text TEXT
)
""")

conn.commit()

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

    cur.execute("SELECT id FROM users WHERE id=?", (uid,))
    if cur.fetchone():
        bot.send_message(uid, "✅ Siz allaqachon ro‘yxatdan o‘tgansiz")
        return

    msg = bot.send_message(uid, "Nik yozing:")
    bot.register_next_step_handler(msg, set_nick)

def set_nick(m):
    uid = str(m.chat.id)
    nick = m.text.strip()

    cur.execute("INSERT INTO users (id, nick) VALUES (?, ?)", (uid, nick))
    conn.commit()

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

    cur.execute("SELECT nick FROM users WHERE id=?", (uid,))
    user = cur.fetchone()
    if not user:
        bot.send_message(uid, "/start bosing")
        return

    msg = bot.send_message(uid, "Sitata yozing:")
    bot.register_next_step_handler(msg, save_quote, user[0])

def save_quote(m, nick):
    text = m.text.strip()
    uid = str(m.chat.id)

    if has_ad(text):
        bot.send_message(uid, "🚫 Reklama mumkin emas")
        return

    cur.execute(
        "INSERT INTO quotes (user_id, author, text) VALUES (?, ?, ?)",
        (uid, nick, text)
    )
    conn.commit()

    bot.send_message(uid, "✅ Saqlandi")

# =====================
# /sitat
# =====================
@bot.message_handler(commands=["sitat"])
def sitat(m):
    cur.execute("SELECT text, author FROM quotes ORDER BY RANDOM() LIMIT 1")
    q = cur.fetchone()

    if not q:
        bot.send_message(m.chat.id, "❌ Sitata yo‘q")
        return

    bot.send_message(m.chat.id, f"“{q[0]}”\n— {q[1]}")

# =====================
# O‘Z SITATALARINI O‘CHIRISH
# =====================
@bot.message_handler(commands=["myquotes"])
def myquotes(m):
    uid = str(m.chat.id)

    cur.execute("SELECT qid, text FROM quotes WHERE user_id=?", (uid,))
    rows = cur.fetchall()

    if not rows:
        bot.send_message(uid, "❌ Sizda sitata yo‘q")
        return

    txt = "🗑 O‘chirish uchun raqam yozing:\n\n"
    for i, r in enumerate(rows):
        txt += f"{i+1}. {r[1]}\n"

    msg = bot.send_message(uid, txt)
    bot.register_next_step_handler(msg, delete_quote, rows)

def delete_quote(m, rows):
    try:
        i = int(m.text) - 1
        qid = rows[i][0]

        cur.execute("DELETE FROM quotes WHERE qid=?", (qid,))
        conn.commit()

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
    cur.execute("SELECT id FROM users")
    users = cur.fetchall()

    sent = 0
    for u in users:
        try:
            bot.copy_message(u[0], m.chat.id, m.message_id)
            sent += 1
        except:
            pass

    bot.send_message(m.chat.id, f"✅ {sent} ta foydalanuvchiga yuborildi")

# =====================
# START
# =====================
print("Sitatabot SQLite bilan ishga tushdi")

while True:
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print("Xato:", e)
        time.sleep(5)
