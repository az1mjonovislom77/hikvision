import requests
from io import BytesIO
from decouple import config
from requests.auth import HTTPDigestAuth

BOT_TOKEN = config("BOT_TOKEN")
print("BOT_TOKEN =", config("BOT_TOKEN", default="YOQ"))


def download_image(url, device):
    try:
        result = requests.get(url, auth=HTTPDigestAuth(device.username, device.password), timeout=15)

        if result.status_code == 200 and result.content:
            return result.content
    except Exception as e:
        print("DOWNLOAD ERROR:", e)

    return None


def send_telegram(chat_id, text, image_bytes=None):
    if image_bytes:
        file_obj = BytesIO(image_bytes)
        file_obj.name = "event.jpg"

        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
            data={
                "chat_id": chat_id,
                "caption": text,
                "parse_mode": "HTML",
            },
            files={"photo": file_obj},
            timeout=15,
        )
    else:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
            },
            timeout=5,
        )

    r.raise_for_status()
