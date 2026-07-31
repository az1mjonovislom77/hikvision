import logging

from decouple import config

from utils.models import TelegramChannel
from utils.telegram.telegram import BASE_URL, session

logger = logging.getLogger(__name__)

BOT_TOKEN = config("BOT_TOKEN")


def sync_channels_from_updates():
    try:
        r = session.get(f"{BASE_URL}/getUpdates", timeout=20)
        r.raise_for_status()
        data = r.json()

    except Exception:
        logger.exception("TELEGRAM GET UPDATES ERROR")
        return

    for update in data.get("result", []):
        message = update.get("channel_post")
        if not message:
            continue

        chat = message.get("chat")
        chat_id = str(chat["id"])
        title = chat.get("title")
        logger.info("📡 Update from channel: %s (%s)", title, chat_id)
        channel = TelegramChannel.objects.filter(name=title, resolved_id__isnull=True).first()

        if channel:
            channel.resolved_id = chat_id
            channel.save(update_fields=["resolved_id"])
            logger.info("✅ Channel resolved: %s → %s", channel.name, chat_id)
