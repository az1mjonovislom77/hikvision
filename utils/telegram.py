import requests
from decouple import config

BOT_TOKEN = config("BOT_TOKEN")
CHAT_ID = config("CHAT_ID")

def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    r = requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        },
        timeout=5
    )

    r.raise_for_status()
