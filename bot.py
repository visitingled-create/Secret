import time
import requests
import threading
from datetime import datetime
from telegram.ext import Updater, CommandHandler

# ==== НАСТРОЙКИ ====
VK_TOKEN = "vk1.a.J4QY_Zu6YFchcBgIybK-3ZVUR-vfasDPnNx-y7mH_Vh4eUWwt9Xcrvy_yYqazQa4NBO8HYEbaPaGQKc9w2sLz7xSlOvVL15Xzt5r539jGRpc3UGoBI4L9SOYGqvMGTHMgEENHHeyDv1GkYs2fKTJC-UGl4fpaQu1vzqWhmYDt0zdm2R_Ysp8L6Jpd8uH4vk7eGInFAtun4dBiO3c_ihiuQ"
TG_TOKEN = "8374206437:AAGBOlC4_3gQAW1oHe0CQXg6hFY1Yc_RwXE"

# список отслеживаемых пользователей {vk_id: tg_chat}
USERS = {}

CHECK_INTERVAL = 5  # секунд между проверками


# ==== VK ====
def get_vk_users(user_ids):
    ids = ",".join(user_ids)
    url = "https://api.vk.com/method/users.get"
    params = {
        "user_ids": ids,
        "fields": "online,domain,first_name,last_name,online_app,online_mobile,last_seen",
        "access_token": VK_TOKEN,
        "v": "5.199"
    }
    resp = requests.get(url, params=params).json()
    try:
        return resp["response"]
    except Exception:
        print("Ошибка VK:", resp)
        return []


def device_name(user):
    """Определяем устройство по данным VK"""
    if user.get("online_mobile"):
        return "📱 Мобильное устройство"
    if user.get("online_app"):
        return f"📲 Приложение VK (id {user['online_app']})"
    if user.get("last_seen", {}).get("platform"):
        platforms = {
            1: "📱 Mobile",
            2: "💻 iPhone",
            3: "📱 iPad",
            4: "💻 Android",
            5: "💻 Windows Phone",
            6: "💻 Windows 10",
            7: "🌐 VK Web"
        }
        return platforms.get(user["last_seen"]["platform"], "📟 Неизвестное устройство")
    return "❓ Неизвестно"


def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    params = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    requests.get(url, params=params)


# ==== TELEGRAM КОМАНДЫ ====
def start(update, context):
    update.message.reply_text("👋 Привет! Я слежу за статусами VK.\n"
                              "Команды:\n"
                              "/add_vk <vk_id> — добавить пользователя\n"
                              "/del_vk <vk_id> — удалить пользователя\n"
                              "/list — список отслеживаемых")


def add_vk(update, context):
    if len(context.args) != 1:
        update.message.reply_text("⚠ Использование: /add_vk <vk_id>")
        return
    vk_id = context.args[0]
    USERS[vk_id] = str(update.message.chat_id)
    update.message.reply_text(f"✅ Пользователь {vk_id} добавлен для отслеживания.")


def del_vk(update, context):
    if len(context.args) != 1:
        update.message.reply_text("⚠ Использование: /del_vk <vk_id>")
        return
    vk_id = context.args[0]
    if vk_id in USERS:
        USERS.pop(vk_id)
        update.message.reply_text(f"❌ Пользователь {vk_id} удалён.")
    else:
        update.message.reply_text("⚠ Этот VK ID не отслеживается.")


def list_users(update, context):
    if not USERS:
        update.message.reply_text("📭 Список пуст.")
    else:
        text = "📌 Отслеживаемые пользователи:\n"
        for vk_id, tg_chat in USERS.items():
            text += f"- VK ID: {vk_id} → Telegram: {tg_chat}\n"
        update.message.reply_text(text)


# ==== ФОН ПРОВЕРКИ ====
def check_loop():
    last_statuses = {}
    while True:
        if USERS:
            users_data = get_vk_users(list(USERS.keys()))
            for user in users_data:
                uid = str(user["id"])
                name = f'{user["first_name"]} {user["last_name"]}'
                link = f'https://vk.com/{user.get("domain", "id"+uid)}'
                status = user.get("online", 0) == 1

                prev_status = last_statuses.get(uid)
                if prev_status is None:
                    last_statuses[uid] = status
                    continue

                if status != prev_status:
                    now = datetime.now().strftime("%H:%M:%S %d.%m.%Y")
                    dev = device_name(user)
                    if status:
                        msg = f"✅ <b>{name}</b> (<code>{uid}</code>)\n<a href='{link}'>Профиль</a>\nЗашёл в сеть в {now}\n{dev}"
                    else:
                        msg = f"❌ <b>{name}</b> (<code>{uid}</code>)\n<a href='{link}'>Профиль</a>\nВышел из сети в {now}"
                    send_telegram_message(USERS[uid], msg)
                    last_statuses[uid] = status
        time.sleep(CHECK_INTERVAL)


# ==== ЗАПУСК ====
if __name__ == "__main__":
    updater = Updater(TG_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("add_vk", add_vk))
    dp.add_handler(CommandHandler("del_vk", del_vk))
    dp.add_handler(CommandHandler("list", list_users))

    # поток проверки статусов
    threading.Thread(target=check_loop, daemon=True).start()

    updater.start_polling()
    updater.idle()
