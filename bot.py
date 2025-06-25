import telebot
import json
import time
import os
from telebot.types import ChatPermissions


print("DEBUG: BOT_TOKEN =", os.getenv("BOT_TOKEN"))
bot_token = os.getenv("BOT_TOKEN")
if not bot_token:
    raise Exception("BOT_TOKEN environment variable not set")
    

bot = telebot.TeleBot(bot_token)

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

from telebot.types import ChatPermissions

@bot.message_handler(commands=['mute'])
def mute_user(message):
    try:
        args = message.text.split()
        if not message.reply_to_message:
            bot.reply_to(message, "Please reply to the user's message you want to mute.")
            return

        if len(args) < 2:
            bot.reply_to(message, "Usage: Reply to a user and use /mute [admin-password] [optional reason]")
            return

        admin_password = args[1]
        reason = " ".join(args[2:]) if len(args) > 2 else "No reason provided"

        if admin_password != "qwertpoiuy":
            bot.reply_to(message, "❌ Incorrect admin password.")
            return

        user_to_mute = message.reply_to_message.from_user
        chat_id = message.chat.id

        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False
        )

        bot.restrict_chat_member(chat_id, user_to_mute.id, permissions)
        bot.reply_to(message, f"✅ Muted {user_to_mute.first_name}. Reason: {reason}")

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")


from telebot.types import ChatPermissions

@bot.message_handler(commands=['unmute'])
def unmute_user(message):
    try:
        args = message.text.split()
        if not message.reply_to_message:
            bot.reply_to(message, "Please reply to the muted user's message.")
            return

        if len(args) < 2:
            bot.reply_to(message, "Usage: Reply to the user and use /unmute [admin-password]")
            return

        admin_password = args[1]

        if admin_password != "qwertpoiuy":
            bot.reply_to(message, "❌ Incorrect admin password.")
            return

        user_to_unmute = message.reply_to_message.from_user
        chat_id = message.chat.id

        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_change_info=False,
            can_invite_users=True,
            can_pin_messages=False
        )

        bot.restrict_chat_member(chat_id, user_to_unmute.id, permissions)
        bot.reply_to(message, f"✅ Unmuted {user_to_unmute.first_name}.")

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

# Catch-all
@bot.message_handler(func=lambda message: message.text.startswith('/'))
def fallback(message):
    bot.reply_to(message, "❓ Unknown command or incorrect usage.")

print("🚀 Bot is running with persistent storage...")
bot.polling()
