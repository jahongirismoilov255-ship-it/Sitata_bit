import telebot
import time
import re

TOKEN = "8142373417:AAHv2Mk3Jn7xPBFhBVtUC7hObERqimgKUqQ"
ADMIN_ID = 7789281265  # o‘zingning Telegram ID

bot = telebot.TeleBot(TOKEN)

# RAM dagi ma’lumotlar (restart bo‘lsa tozalanadi)
users = set()
last_send = {}  # spamdan himoya

SPAM_LIMIT = 600  # 10 daqiqa (soniya)

# =====================
# START
# =====================
@bot.message_handler(commands=['start'])
def start(msg):
    users.add(msg.chat.id)
    bot.reply_to(
        msg,
        "👋 Salom!\n\n"
        "Bu ochiq e’lon bot.\n"
        "📝 Text yoki 🔗 link yuborsang — hamma foydalanuvchiga 1 marta boradi.\n\n"
        "❗ Spam qilmang."
    )

# =====================
# ADMIN PANEL
# =====================
@bot.message_handler(commands=['admin'])
def admin_panel(msg):
    if msg.chat.id == ADMIN_ID:
        bot.reply_to(msg, "👑 Admin panel:\n\n/send — hammaga xabar yuborish")
    else:
        bot.reply_to(msg, "⛔ Siz admin emassiz")

@bot.message_handler(commands=['send'])
def admin_send(msg):
    if msg.chat.id != ADMIN_ID:
        return

    sent = bot.send_message(msg.chat.id, "📢 Hammaga yuboriladigan xabarni yozing:")
    bot.register_next_step_handler(sent, broadcast_admin)

def broadcast_admin(msg):
    for uid in users:
        try:
            bot.send_message(uid, f"🔔 ADMIN E’LONI:\n\n{msg.text}")
        except:
            pass
    bot.reply_to(msg, "✅ Yuborildi")

# =====================
# USER E’LONLARI
# =====================
@bot.message_handler(func=lambda m: True, content_types=['text'])
def user_ads(msg):
    uid = msg.chat.id
    users.add(uid)

    # admin buyruqlarini o‘tkazib yuborish
    if msg.text.startswith('/'):
        return

    now = time.time()
    if uid in last_send and now - last_send[uid] < SPAM_LIMIT:
        bot.reply_to(msg, "⏳ Keyinroq yuboring (10 daqiqa limit).")
        return

    # oddiy tekshiruv
    if len(msg.text) > 500:
        bot.reply_to(msg, "❌ Juda uzun xabar.")
        return

    if re.search(r"(porn|18\+|casino)", msg.text.lower()):
        bot.reply_to(msg, "❌ Taqiqlangan kontent.")
        return

    # hammaga yuborish
    for user in users:
        try:
            bot.send_message(
                user,
                f"📣 YANGI E’LON:\n\n{msg.text}\n\n👤 @{msg.from_user.username or 'NoUsername'}"
            )
        except:
            pass

    last_send[uid] = now
    bot.reply_to(msg, "✅ E’lon yuborildi")

# =====================
# BOT START
# =====================
print("Bot ishga tushdi...")
bot.infinity_polling(skip_pending=True)
