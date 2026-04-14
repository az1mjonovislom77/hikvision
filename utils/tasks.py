from celery import shared_task
import logging
import time

from event.models import AccessEvent
from utils.models import TelegramChannel, Devices
from utils.telegram.telegram import download_image, send_telegram

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=10,
    retry_kwargs={"max_retries": 5},
    rate_limit="20/m"
)
def send_event_to_telegram(self, event_id, msg, picture_url, device_id):
    try:
        event = AccessEvent.objects.get(id=event_id)
        device = Devices.objects.get(id=device_id)
    except Exception:
        logger.exception("EVENT or DEVICE NOT FOUND")
        return

    image_bytes = None

    if picture_url and device.username and device.password:
        try:
            image_bytes = download_image(picture_url, device)
        except Exception:
            logger.exception("IMAGE DOWNLOAD FAILED")

    channels = TelegramChannel.objects.filter(
        device=device,
        resolved_id__isnull=False
    )

    success_count = 0

    for channel in channels:
        try:
            send_telegram(
                chat_id=channel.resolved_id,
                text=msg,
                image_bytes=image_bytes
            )
            success_count += 1

            time.sleep(0.3)

        except Exception:
            logger.exception(f"Telegram send failed: {channel.resolved_id}")

    if success_count > 0:
        event.sent_to_telegram = True
        event.save(update_fields=["sent_to_telegram"])
    else:
        raise Exception("All telegram sends failed")
