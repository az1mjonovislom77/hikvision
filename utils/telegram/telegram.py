import logging
import requests
import socket
from io import BytesIO
from decouple import config
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests.auth import HTTPDigestAuth

logger = logging.getLogger(__name__)

BOT_TOKEN = config("BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def force_ipv4():
    return socket.AF_INET


requests.packages.urllib3.util.connection.allowed_gai_family = force_ipv4

session = requests.Session()

retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])

adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)
session.mount("http://", adapter)


def download_image(url, device):
    try:
        r = session.get(url, auth=HTTPDigestAuth(device.username, device.password), timeout=20)
        if r.status_code == 200 and r.content:
            return r.content
    except requests.exceptions.RequestException:
        logger.exception("DOWNLOAD IMAGE ERROR")

    return None


def send_telegram(chat_id, text, image_bytes=None):
    try:
        if image_bytes:
            file_obj = BytesIO(image_bytes)
            file_obj.name = "event.jpg"

            r = session.post(
                f"{BASE_URL}/sendPhoto",
                data={
                    "chat_id": chat_id,
                    "caption": text,
                    "parse_mode": "HTML"
                },
                files={"photo": file_obj},
                timeout=20
            )
        else:
            r = session.post(
                f"{BASE_URL}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML"
                },
                timeout=20
            )

        logger.info(f"Telegram response: {r.text}")

    except requests.exceptions.RequestException:
        logger.exception("TELEGRAM SEND ERROR")
