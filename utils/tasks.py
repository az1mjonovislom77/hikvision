import logging
import time

from celery import shared_task

from event.models import AccessEvent
from utils.models import Devices, TelegramChannel
from utils.telegram.telegram import download_image, send_telegram

logger = logging.getLogger(__name__)


@shared_task(
    bind=True, autoretry_for=(Exception,), retry_backoff=10, retry_kwargs={"max_retries": 5}, rate_limit="20/m"
)
def send_event_to_telegram(self, event_id, msg, picture_url, device_id):
    event = AccessEvent.objects.get(id=event_id)
    device = Devices.objects.get(id=device_id)

    image_bytes = None

    if picture_url and device.username and device.password:
        image_bytes = download_image(picture_url, device)

    channels = TelegramChannel.objects.filter(device=device, resolved_id__isnull=False)

    for channel in channels:
        try:
            send_telegram(chat_id=channel.resolved_id, text=msg, image_bytes=image_bytes)
            time.sleep(0.3)

        except Exception:
            logger.exception("Telegram send failed: %s", channel.resolved_id)
            raise

    event.sent_to_telegram = True
    event.save(update_fields=["sent_to_telegram"])
