import requests
import logging
from decouple import config
from utils.models import TelegramChannel

logger = logging.getLogger(__name__)

BOT_TOKEN = config("BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def sync_channels_from_updates():
    """
    Private kanal / group bo‘lsa ham
    bot tushgan channel_post orqali
    chat_id ni avtomatik ushlab oladi
    """

    r = requests.get(f"{BASE_URL}/getUpdates", timeout=10)
    r.raise_for_status()

    data = r.json()
    if not data.get("ok"):
        return

    for update in data.get("result", []):
        message = (
            update.get("channel_post")
            or update.get("edited_channel_post")
        )

        if not message:
            continue

        chat = message.get("chat")
        if not chat:
            continue

        chat_id = str(chat.get("id"))
        title = chat.get("title", "")

        logger.info(f"Found channel update: {title} ({chat_id})")

        # resolved_id yo‘q bo‘lgan birinchi kanalni bog‘laymiz
        channel = (
            TelegramChannel.objects
            .filter(resolved_id__isnull=True)
            .order_by("id")
            .first()
        )

        if channel:
            channel.resolved_id = chat_id
            channel.save(update_fields=["resolved_id"])

            logger.info(
                f"Channel resolved: {channel.chat_id} → {chat_id}"
            )
