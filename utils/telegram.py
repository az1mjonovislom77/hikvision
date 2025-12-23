import logging
import requests
from io import BytesIO
from decouple import config
from requests.auth import HTTPDigestAuth

logger = logging.getLogger(__name__)

BOT_TOKEN = config("BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def download_image(url, device):
    try:
        r = requests.get(url, auth=HTTPDigestAuth(device.username, device.password), timeout=15)
        if r.status_code == 200 and r.content:
            return r.content
    except Exception:
        logger.exception("DOWNLOAD IMAGE ERROR")
    return None


def send_telegram(chat_id, text, image_bytes=None):
    if image_bytes:
        file_obj = BytesIO(image_bytes)
        file_obj.name = "event.jpg"

        r = requests.post(f"{BASE_URL}/sendPhoto", data={"chat_id": chat_id, "caption": text, "parse_mode": "HTML"},
                          files={"photo": file_obj}, timeout=15)
    else:
        r = requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": text, "parse_mode": "HTML", },
                          timeout=10)

    logger.info(f"Telegram response: {r.text}")
    r.raise_for_status()
