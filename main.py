import telebot
import pyotp
import requests
import random
import time
import os
import threading
from flask import Flask

# --- কনফিগারেশন ---
# আপনার বটের টোকেন
TOKEN = '8619212784:AAGNRWitsKF5EScwGnTvhUMAzatrGjj2Glo' 
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# আপনার দেওয়া অ্যাপস স্ক্রিপ্ট লিঙ্ক
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyPUCH-LmF-WOs6SyTYJ0zXtEtqA__YzSDJpLkMTjZmbHgnWpCYb8FT3iDcO97ar-pQ/exec"

# নমুনা ডাটা (এখানে আপনি আপনার রিয়েল ডাটা দিতে পারেন)
random_data = [
    {"email": "user1@hotmail.com", "pass": "pass123", "name": "Tanjim User 1"},
    {"email": "user2@hotmail.com", "pass": "pass456", "name": "Tanjim User 2"},
]

user_tasks = {}

# --- ওয়েব সার্ভার (Render হোস্টিং সচল রাখার জন্য) ---
@app.route('/')
def home():
    return "Bot is Running Live!"

# --- মেইন মেনু ---
def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('🧾 কাজ শুরু', '💰 প্রোফাইল', '👥 রেফার', '🏆 টপ ইউজার', '📞 সাপোর্ট')
    return markup

# --- কমান্ড হ্যান্ডলার ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "✨ স্বাগতম! কাজ শুরু করতে নিচের বাটনে চাপুন।", reply_markup=main_menu())

# --- কাজ শুরু লজিক ---
@bot.message_handler(func=lambda message: message.text == "🧾 কাজ শুরু")
def start_work(message):
    task = random.choice(random_data)
    user_tasks[message.chat.id] = task
    
    text = (f"╔════════════════════════╗\n"
            f"      📝 নতুন টাস্ক বরাদ্দ 📝\n"
            f"╚════════════════════════╝\n"
            f"👤 নাম: {task['name']}\n"
            f"📧 মেইল: {task['email']}\n"
            f"🔑 পাস: {task['pass']}\n\n"
            f"👇 কোড পেতে নিচে ক্লিক করুন:")
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("📩 মেইল ওটিপি দেখুন", callback_data="get_mail_otp"))
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "get_mail_otp")
def mail_otp(call):
    # র্যান্ডম ওটিপি জেনারেট (নমুনা)
    fake_otp = str(random.randint(100000, 999999))
    bot.edit_message_text(f"✅ মেইল ওটিপি পাওয়া গেছে: `{fake_otp}`\n\nএখন আপনার **2FA Key** টি মেসেজ বক্সে লিখে পাঠান।", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    bot.register_next_step_handler(call.message, get_2fa_key)

def get_2fa_key(message):
    key = message.text.replace(" ", "")
    try:
        totp = pyotp.TOTP(key)
        otp_2fa = totp.now()
        user_tasks[message.chat.id]['2fa_key'] = key
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("✅ কাজটি সফল হয়েছে", callback_data="final_submit"))
        bot.send_message(message.chat.id, f"🔐 আপনার ২এফএ ওটিপি: `{otp_2fa}`\n\nকাজটি শেষ হলে নিচের বাটনে ক্লিক করুন।", reply_markup=markup, parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "❌ ভুল 2FA Key! আবার চেষ্টা করুন।")

@bot.callback_query_handler(func=lambda call: call.data == "final_submit")
def final_submit(call):
    data = user_tasks.get(call.message.chat.id)
    if data:
        # গুগল শিটে ডাটা পাঠানো
        row_data = [str(time.ctime()), str(call.from_user.id), data['email'], data['pass'], data['2fa_key'], "Pending"]
        try:
            requests.post(WEB_APP_URL, json={"row": row_data}, timeout=10)
            bot.edit_message_text("🎉 অভিনন্দন! আপনার কাজটি সফলভাবে জমা হয়েছে।", call.message.chat.id, call.message.message_id)
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ গুগল শিটে সেভ করা যায়নি। এরর: {e}")

# --- রান করার ফাংশন ---
def run_web():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    threading.Thread(target=run_web).start()
    print("✅ System Started Successfully")
    bot.infinity_polling()
      
