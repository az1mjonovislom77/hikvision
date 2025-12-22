import requests
from io import BytesIO
from decouple import config
from requests.auth import HTTPDigestAuth

BOT_TOKEN = config("BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def download_image(url, device):
    try:
        r = requests.get(
            url,
            auth=HTTPDigestAuth(device.username, device.password),
            timeout=15
        )
        if r.status_code == 200 and r.content:
            return r.content
    except Exception as e:
        print("DOWNLOAD ERROR:", e)
    return None
def resolve_chat_id(chat_id_raw):

    if not chat_id_raw:
        return None

    chat_id_raw = chat_id_raw.strip()


    if chat_id_raw.lstrip("-").isdigit():
        return chat_id_raw

    # t.me/username → @username
    if "t.me/" in chat_id_raw:
        chat_id_raw = "@" + chat_id_raw.split("t.me/")[-1]

    if not chat_id_raw.startswith("@"):
        chat_id_raw = "@" + chat_id_raw

    # Telegram API orqali tekshirish
    r = requests.get(
        f"{BASE_URL}/getChat",
        params={"chat_id": chat_id_raw},
        timeout=10
    )

    r.raise_for_status()
    data = r.json()

    return str(data["result"]["id"])


def send_telegram(chat_id, text, image_bytes=None):
    chat_id = resolve_chat_id(chat_id)

    if not chat_id:
        raise ValueError("CHAT_ID ANIQLANMADI")

    if image_bytes:
        file_obj = BytesIO(image_bytes)
        file_obj.name = "event.jpg"

        r = requests.post(
            f"{BASE_URL}/sendPhoto",
            data={
                "chat_id": chat_id,
                "caption": text,
                "parse_mode": "HTML",
            },
            files={"photo": file_obj},
            timeout=15
        )
    else:
        r = requests.post(
            f"{BASE_URL}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
            },
            timeout=10
        )

    r.raise_for_status()
