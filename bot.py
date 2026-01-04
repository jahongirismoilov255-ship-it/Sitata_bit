import telebot
import re
import random
import time

TOKEN = "BOT_TOKENINGNI_BU_YERGA_QO‘Y"
bot = telebot.TeleBot(TOKEN)

# =======================
# MA'LUMOTLAR (oddiy variant)
# =======================

users = {}      # user_id: {lang, nick, step}
nicks = set()   # band niklar
quotes = []     # {text, lang, author}

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
    user_id = message.chat.id
    users[user_id] = {"step": "lang"}

    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🇺🇿 O‘zbek", "🇹🇯 Тоҷикӣ", "🇷🇺 Русский")

    bot.send_message(
        user_id,
        "Tilni tanlang:",
        reply_markup=kb
    )

# =======================
# TIL TANLASH
# =======================

@bot.message_handler(func=lambda m: m.chat.id in users and users[m.chat.id]["step"] == "lang")
def set_lang(message):
    user_id = message.chat.id
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

    bot.send_message(
        user_id,
        "Nik tanlang (unikal bo‘lishi shart):",
        reply_markup=telebot.types.ReplyKeyboardRemove()
    )

# =======================
# NIK TANLASH
# =======================

@bot.message_handler(func=lambda m: m.chat.id in users and users[m.chat.id]["step"] == "nick")
def set_nick(message):
    user_id = message.chat.id
    nick = message.text.strip()

    if nick in nicks:
        bot.send_message(user_id, "❌ Bu nik band, boshqasini tanlang")
        return

    nicks.add(nick)
    users[user_id]["nick"] = nick
    users[user_id]["step"] = "done"

    bot.send_message(
        user_id,
        f"✅ Ro‘yxatdan o‘tdingiz!\nNikingiz: {nick}\n\n/post — sitata joylash\n/sitat — sitata ko‘rish"
    )

# =======================
# POST QO‘SHISH
# =======================

@bot.message_handler(commands=['post'])
def post_quote(message):
    user_id = message.chat.id

    if user_id not in users or users[user_id].get("step") != "done":
        bot.send_message(user_id, "❌ Avval ro‘yxatdan o‘ting (/start)")
        return

    msg = bot.send_message(user_id, "Sitata yozing:")
    bot.register_next_step_handler(msg, save_quote)

def save_quote(message):
    user_id = message.chat.id
    text = message.text.strip()

    # REKLAMA TEKSHIRUV
    if has_ad(text):
        bot.send_message(
            user_id,
            "🚫 Reklama qilmang!\nLink aniqlandi.\nPost bekor qilindi."
        )
        return

    quote = {
        "text": text,
        "lang": users[user_id]["lang"],
        "author": users[user_id]["nick"]
    }

    quotes.append(quote)

    bot.send_message(user_id, "✅ Sitata muvaffaqiyatli joylandi")

# =======================
# /sitat
# =======================

@bot.message_handler(commands=['sitat'])
def get_quote(message):
    user_id = message.chat.id

    if user_id not in users or users[user_id].get("step") != "done":
        bot.send_message(user_id, "❌ Avval ro‘yxatdan o‘ting (/start)")
        return

    lang = users[user_id]["lang"]
    lang_quotes = [q for q in quotes if q["lang"] == lang]

    if not lang_quotes:
        bot.send_message(user_id, "❌ Hozircha sitatalar yo‘q")
        return

    q = random.choice(lang_quotes)

    bot.send_message(
        user_id,
        f"“{q['text']}”\n\n— {q['author']}"
    )

# =======================
# SERVER UCHUN ISHGA TUSHIRISH
# =======================

print("Bot ishga tushdi...")
while True:
    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        print("Xatolik:", e)
        time.sleep(5)
