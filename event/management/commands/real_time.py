import time
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from event.services.event_state import get_last_event_time, set_last_event_time
from event.services.event_sync import fetch_face_events
from event.models import AccessEvent
from utils.models import TelegramChannel, Devices
from utils.telegram.telegram import download_image, send_telegram
from utils.telegram.telegram_updates import sync_channels_from_updates

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Realtime Hikvision events → Telegram channel"

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Realtime event listener started")

        last_time = get_last_event_time()
        if last_time is None:
            last_event = AccessEvent.objects.order_by("-time").first()
            last_time = last_event.time if last_event else timezone.now()

        while True:
            try:
                sync_channels_from_updates()

                devices = Devices.objects.all()
                fetch_face_events(devices=devices, since=last_time)

                events = (AccessEvent.objects.filter(time__gt=last_time, sent_to_telegram=False)
                          .select_related("employee", "device", "device__user").order_by("time"))

                for event in events:
                    employee = event.employee
                    device = event.device

                    if not employee or not device or not device.user:
                        event.sent_to_telegram = True
                        event.save(update_fields=["sent_to_telegram"])
                        continue

                    raw = event.raw_json or {}
                    label = (raw.get("labelName") or raw.get("label") or raw.get("name") or "").strip().lower()

                    direction = (
                        "🚪 KIRISH" if label in {"kirish", "in", "entry", "enter"}
                        else "🚷 CHIQISH" if label in {"chiqish", "out", "exit", "leave"} else "❓ NOMAʼLUM"
                    )

                    msg = (
                        f"<b>{direction}</b>\n\n"
                        f"👤 <b>Ism:</b> {employee.name}\n"
                        f"🆔 <b>Employee №:</b> {employee.employee_no}\n"
                        f"🕒 <b>Vaqt:</b> {event.time:%Y-%m-%d %H:%M:%S}\n"
                        f"📍 <b>Qurilma:</b> {device.name}"
                    )

                    image_bytes = None
                    picture_url = raw.get("pictureURL") or raw.get("faceURL")

                    if picture_url and device.username and device.password:
                        image_bytes = download_image(picture_url, device)

                    channels = TelegramChannel.objects.filter(user=device.user, resolved_id__isnull=False)

                    for channel in channels:
                        try:
                            send_telegram(chat_id=channel.resolved_id, text=msg, image_bytes=image_bytes)
                        except Exception:
                            logger.exception(f"Telegram send failed: {channel.resolved_id}")

                    event.sent_to_telegram = True
                    event.save(update_fields=["sent_to_telegram"])

                    last_time = event.time
                    set_last_event_time(last_time)

            except Exception:
                logger.exception("MAIN LOOP ERROR")

            time.sleep(5)
