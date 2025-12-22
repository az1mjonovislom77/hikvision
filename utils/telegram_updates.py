import requests
import logging
from decouple import config
from utils.models import TelegramChannel

logger = logging.getLogger(__name__)

BOT_TOKEN = config("BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def sync_channels_from_updates():
    r = requests.get(f"{BASE_URL}/getUpdates", timeout=10)
    r.raise_for_status()
    data = r.json()

    for update in data.get("result", []):
        message = update.get("channel_post")
        if not message:
            continue

        chat = message.get("chat")
        chat_id = str(chat["id"])
        title = chat.get("title")

        logger.info(f"📡 Update from channel: {title} ({chat_id})")

        # 🔑 TITLE ORQALI MATCH QILAMIZ
        channel = TelegramChannel.objects.filter(
            name=title,
            resolved_id__isnull=True
        ).first()

        if channel:
            channel.resolved_id = chat_id
            channel.save(update_fields=["resolved_id"])

            logger.info(
                f"✅ Channel resolved: {channel.name} → {chat_id}"
            )
