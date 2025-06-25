import telebot
import json
import os
from telebot.types import ChatPermissions

BOT_TOKEN = os.getenv('8199674703:AAFozO9y2x2J4wNhvRMsnbj634v-Drj7iwE')
bot = telebot.TeleBot(BOT_TOKEN)

OWNER_PASSWORD = 'e7uoe6aA3'
ADMIN_PASSWORD = 'qwertpoiuy'

DATA_FILE = 'data.json'

# ========== PERSISTENT STORAGE ==========

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"owners": [], "admins": [], "muted": []}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

data = load_data()

def is_owner(username):
    return username.lower() in data["owners"]

def is_admin(username):
    return username.lower() in data["admins"] or is_owner(username)

def add_owner(username):
    if username.lower() not in data["owners"]:
        data["owners"].append(username.lower())
        save_data()

def add_admin(username):
    if username.lower() not in data["admins"]:
        data["admins"].append(username.lower())
        save_data()

def remove_admin(username):
    if username.lower() in data["admins"]:
        data["admins"].remove(username.lower())
        save_data()

def mute_user(username):
    if username.lower() not in data["muted"]:
        data["muted"].append(username.lower())
        save_data()

def unmute_user(username):
    if username.lower() in data["muted"]:
        data["muted"].remove(username.lower())
        save_data()

def is_muted(username):
    return username.lower() in data["muted"]

# ========== COMMAND HANDLERS ==========

@bot.message_handler(commands=['owner'])
def cmd_owner(message):
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "Usage: /owner @user owner-password")
        return

    username = args[1].lstrip('@')
    password = args[2]

    if password != OWNER_PASSWORD:
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

    target = args[1].lstrip('@')
    password = args[2]
    sender = message.from_user.username or ""

    if not is_owner(sender):
        bot.reply_to(message, "❌ Only owners can assign admins.")
        return

    if password != OWNER_PASSWORD:
        bot.reply_to(message, "Invalid owner password.")
        return

    add_admin(target)
    bot.reply_to(message, f"✅ @{target} is now an admin.")

@bot.message_handler(commands=['unadmin'])
def cmd_unadmin(message):
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "Usage: /unadmin @user owner-password")
        return

    target = args[1].lstrip('@')
    password = args[2]
    sender = message.from_user.username or ""

    if not is_owner(sender):
        bot.reply_to(message, "❌ Only owners can remove admins.")
        return

    if password != OWNER_PASSWORD:
        bot.reply_to(message, "Invalid owner password.")
        return

    remove_admin(target)
    bot.reply_to(message, f"✅ @{target} is no longer an admin.")

@bot.message_handler(commands=['mute'])
def cmd_mute(message):
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "Usage: /mute @user admin-password [reason]")
        return

    target = args[1].lstrip('@')
    password = args[2]
    reason = " ".join(args[3:]) if len(args) > 3 else "No reason provided"
    sender = message.from_user.username or ""

    if not is_admin(sender):
        bot.reply_to(message, "❌ Only admins or owners can mute.")
        return

    if password != ADMIN_PASSWORD:
        bot.reply_to(message, "Invalid admin password.")
        return

    if is_admin(target):
        bot.reply_to(message, "❌ You can't mute an admin or owner.")
        return

    mute_user(target)
    try:
        user = bot.get_chat_member(message.chat.id, message.reply_to_message.from_user.id).user
        bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
    except:
        pass
    bot.reply_to(message, f"🔇 @{target} has been muted.\nReason: {reason}")

@bot.message_handler(commands=['unmute'])
def cmd_unmute(message):
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "Usage: /unmute @user admin-password")
        return

    target = args[1].lstrip('@')
    password = args[2]
    sender = message.from_user.username or ""

    if not is_admin(sender):
        bot.reply_to(message, "❌ Only admins or owners can unmute.")
        return

    if password != ADMIN_PASSWORD:
        bot.reply_to(message, "Invalid admin password.")
        return

    if not is_muted(target):
        bot.reply_to(message, f"@{target} is not muted.")
        return

    unmute_user(target)
    try:
        user = bot.get_chat_member(message.chat.id, message.reply_to_message.from_user.id).user
        bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user.id,
            permissions=ChatPermissions(can_send_messages=True)
        )
    except:
        pass
    bot.reply_to(message, f"✅ @{target} has been unmuted.")

# Catch-all
@bot.message_handler(func=lambda message: message.text.startswith('/'))
def fallback(message):
    bot.reply_to(message, "❓ Unknown command or incorrect usage.")

print("🚀 Bot is running with persistent storage...")
bot.polling()
