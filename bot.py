import os
import json
from flask import Flask, request
import telebot
from telebot.types import ChatPermissions

# Setup
bot_token = os.getenv("BOT_TOKEN")
if not bot_token:
    raise Exception("BOT_TOKEN environment variable not set")

bot = telebot.TeleBot(bot_token)
app = Flask(__name__)

OWNER_PASSWORD = 'e7uoe6aA3'
ADMIN_PASSWORD = 'qwertpoiuy'
DATA_FILE = 'data.json'

@app.before_first_request
def setup_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=os.getenv("WEBHOOK_URL"))

@app.route('/webhook', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '', 200


# ========== Persistent Storage ==========
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"owners": [], "admins": [], "muted": []}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

data = load_data()

# ========== Helpers ==========
def is_owner(username): return username.lower() in data["owners"]
def is_admin(username): return username.lower() in data["admins"] or is_owner(username)
def add_owner(username): data["owners"].append(username.lower()); save_data()
def add_admin(username): data["admins"].append(username.lower()); save_data()
def remove_admin(username): data["admins"].remove(username.lower()); save_data()
def mute_user(username): data["muted"].append(username.lower()); save_data()
def unmute_user(username): data["muted"].remove(username.lower()); save_data()
def is_muted(username): return username.lower() in data["muted"]

# ========== Command Handlers ==========
@bot.message_handler(commands=['owner'])
def cmd_owner(message):
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "Usage: /owner @user owner-password")
        return
    username = args[1].lstrip('@')
    if args[2] != OWNER_PASSWORD:
        bot.reply_to(message, "Invalid owner password.")
        return
    add_owner(username)
    bot.reply_to(message, f"✅ @{username} is now an owner.")

@bot.message_handler(commands=['admin'])
def cmd_admin(message):
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "Usage: /admin @user owner-password")
        return
    sender = message.from_user.username or ""
    if not is_owner(sender) or args[2] != OWNER_PASSWORD:
        bot.reply_to(message, "❌ Only owners can assign admins.")
        return
    add_admin(args[1].lstrip('@'))
    bot.reply_to(message, f"✅ @{args[1]} is now an admin.")

@bot.message_handler(commands=['unadmin'])
def cmd_unadmin(message):
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "Usage: /unadmin @user owner-password")
        return
    sender = message.from_user.username or ""
    if not is_owner(sender) or args[2] != OWNER_PASSWORD:
        bot.reply_to(message, "❌ Only owners can remove admins.")
        return
    remove_admin(args[1].lstrip('@'))
    bot.reply_to(message, f"✅ @{args[1]} is no longer an admin.")

@bot.message_handler(commands=['mute'])
def handle_mute(message):
    if not message.reply_to_message:
        bot.reply_to(message, "Please reply to the user's message you want to mute.")
        return
    args = message.text.split()
    if len(args) < 2 or args[1] != ADMIN_PASSWORD:
        bot.reply_to(message, "Usage: /mute [admin-password] [reason]\n❌ Incorrect admin password.")
        return
    reason = " ".join(args[2:]) if len(args) > 2 else "No reason provided"
    user = message.reply_to_message.from_user
    chat_id = message.chat.id
    bot.restrict_chat_member(chat_id, user.id, ChatPermissions())
    bot.reply_to(message, f"✅ Muted {user.first_name}. Reason: {reason}")

@bot.message_handler(commands=['unmute'])
def handle_unmute(message):
    if not message.reply_to_message:
        bot.reply_to(message, "Please reply to the user's message you want to unmute.")
        return
    args = message.text.split()
    if len(args) < 2 or args[1] != ADMIN_PASSWORD:
        bot.reply_to(message, "Usage: /unmute [admin-password]\n❌ Incorrect admin password.")
        return
    user = message.reply_to_message.from_user
    chat_id = message.chat.id
    perms = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
        can_change_info=False,
        can_invite_users=True,
        can_pin_messages=False
    )
    bot.restrict_chat_member(chat_id, user.id, perms)
    bot.reply_to(message, f"✅ Unmuted {user.first_name}.")

@bot.message_handler(func=lambda message: message.text.startswith('/'))
def fallback(message):
    bot.reply_to(message, "❓ Unknown command or incorrect usage.")

# ========== Flask Webhook ==========
@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def index():
    return "🤖 Bot is running (webhook mode).", 200

# ========== Set webhook on startup ==========
if __name__ == "__main__":
    webhook_url = os.getenv("WEBHOOK_URL")  # e.g. https://your-app-name.onrender.com/webhook
    if not webhook_url:
        raise Exception("WEBHOOK_URL environment variable not set")
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
