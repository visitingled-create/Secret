import time
import requests
from datetime import datetime

# ==== НАСТРОЙКИ ====
VK_TOKEN = "vk1.a.J4QY_Zu6YFchcBgIybK-3ZVUR-vfasDPnNx-y7mH_Vh4eUWwt9Xcrvy_yYqazQa4NBO8HYEbaPaGQKc9w2sLz7xSlOvVL15Xzt5r539jGRpc3UGoBI4L9SOYGqvMGTHMgEENHHeyDv1GkYs2fKTJC-UGl4fpaQu1vzqWhmYDt0zdm2R_Ysp8L6Jpd8uH4vk7eGInFAtun4dBiO3c_ihiuQ"
TG_TOKEN = "8374206437:AAGBOlC4_3gQAW1oHe0CQXg6hFY1Yc_RwXE"

USERS = [
    {"vk_id": "569477394", "tg_chat": "8017072069"},       # Павел Дуров → твой чат
    {"vk_id": "607870034", "tg_chat": "8017072069"},# Иван → друг
    {"vk_id": "671717895", "tg_chat": "8017072069"} # Катя → третий чат
]

CHECK_INTERVAL = 1  # секунд между проверками

# ==== ФУНКЦИИ ====
def get_vk_users(users):
    ids = ",".join([u["vk_id"] for u in users])
    url = "https://api.vk.com/method/users.get"
    params = {
        "user_ids": ids,
        "fields": "online,domain,first_name,last_name",
        "access_token": VK_TOKEN,
        "v": "5.199"
    }
    resp = requests.get(url, params=params).json()
    try:
        return resp["response"]
    except Exception:
        print("Ошибка VK:", resp)
        return []

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    params = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    requests.get(url, params=params)

# ==== ОСНОВНОЙ ЦИКЛ ====
if __name__ == "__main__":
    last_statuses = {}

    print("Бот запущен. Проверяю статусы пользователей...")

    while True:
        users_data = get_vk_users(USERS)
        for user in users_data:
            uid = str(user["id"])
            name = f'{user["first_name"]} {user["last_name"]}'
            link = f'https://vk.com/{user.get("domain", "id"+uid)}'
            status = user.get("online", 0) == 1

            # ищем "наблюдателя"
            observer = next((u for u in USERS if u["vk_id"] == uid), None)
            if not observer:
                continue
            tg_chat = observer["tg_chat"]

            prev_status = last_statuses.get(uid)
            if prev_status is None:
                last_statuses[uid] = status
                continue

            if status != prev_status:
                now = datetime.now().strftime("%H:%M:%S %d.%m.%Y")
                if status:
                    msg = f"✅ <b>{name}</b> (<code>{uid}</code>)\n<a href='{link}'>Профиль ВК</a>\nЗашёл в сеть в {now}"
                else:
                    msg = f"❌ <b>{name}</b> (<code>{uid}</code>)\n<a href='{link}'>Профиль ВК</a>\nВышел из сети в {now}"
                send_telegram_message(tg_chat, msg)
                last_statuses[uid] = status

        time.sleep(CHECK_INTERVAL)

