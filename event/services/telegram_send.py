import logging
import time

from django.utils import timezone

from utils.models import TelegramChannel
from utils.telegram.telegram import download_image, send_telegram

logger = logging.getLogger(__name__)


def build_message(event):
    employee = event.employee
    device = event.device
    raw = event.raw_json or {}

    label = (raw.get("labelName") or raw.get("label") or raw.get("name") or "").strip().lower()

    direction = (
        "🚪 KIRISH"
        if label in {"kirish", "in", "entry", "enter"}
        else "🚷 CHIQISH"
        if label in {"chiqish", "out", "exit", "leave"}
        else "❓ NOMAʼLUM"
    )

    local_time = timezone.localtime(event.time)

    return (
        f"<b>{direction}</b>\n\n"
        f"👤 <b>Ism:</b> {employee.name}\n"
        f"🆔 <b>Employee №:</b> {employee.employee_no}\n"
        f"🕒 <b>Vaqt:</b> {local_time:%Y-%m-%d %H:%M:%S}\n"
        f"📍 <b>Qurilma:</b> {device.name}"
    )


def send_event(event, per_channel_delay=0.3):
    employee = event.employee
    device = event.device

    if not employee or not device or not device.user:
        event.sent_to_telegram = True
        event.save(update_fields=["sent_to_telegram"])
        return False

    msg = build_message(event)

    raw = event.raw_json or {}
    picture_url = raw.get("pictureURL") or raw.get("faceURL")

    image_bytes = None
    if picture_url and device.username and device.password:
        image_bytes = download_image(picture_url, device)

    channels = list(TelegramChannel.objects.filter(device=device, resolved_id__isnull=False))

    if not channels:
        logger.warning(
            "No resolved telegram channel for device_id=%s (%s) — event %s not sent",
            device.id,
            device.name,
            event.id,
        )
        event.sent_to_telegram = True
        event.save(update_fields=["sent_to_telegram"])
        return False

    sent_any = False
    for channel in channels:
        try:
            send_telegram(chat_id=channel.resolved_id, text=msg, image_bytes=image_bytes)
            sent_any = True
            time.sleep(per_channel_delay)
        except Exception:
            logger.exception("Telegram send failed: %s", channel.resolved_id)

    if not sent_any:
        logger.error("Event %s: all channel sends failed", event.id)
        return False

    event.sent_to_telegram = True
    event.save(update_fields=["sent_to_telegram"])
    return True
