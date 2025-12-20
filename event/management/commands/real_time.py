from django.core.management.base import BaseCommand
import time
from django.utils import timezone
from event.services.event_state import get_last_event_time, set_last_event_time
from event.services.event_sync import fetch_face_events
from event.models import AccessEvent
from utils.models import TelegramChannel
from utils.telegram import send_telegram, download_image
from utils.models import Devices


class Command(BaseCommand):
    help = "Realtime Hikvision events → Telegram channel (every 5 sec)"

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Realtime event listener started")

        last_time = get_last_event_time()

        if last_time is None:
            last_event = AccessEvent.objects.order_by("-time").first()
            last_time = last_event.time if last_event else timezone.now()

        while True:
            try:
                devices = Devices.objects.all()
                fetch_face_events(devices=devices, since=last_time)

                events = (
                    AccessEvent.objects
                    .filter(time__gt=last_time, sent_to_telegram=False)
                    .select_related("employee", "device", "device__user")
                    .order_by("time")
                )

                for event in events:
                    employee = event.employee
                    device = event.device

                    if not employee or not device or not device.user:
                        event.sent_to_telegram = True
                        event.save(update_fields=["sent_to_telegram"])
                        continue

                    raw = event.raw_json or {}

                    label = (
                            raw.get("labelName")
                            or raw.get("label")
                            or raw.get("name")
                            or ""
                    ).strip().lower()

                    if label in {"kirish", "in", "entry", "enter"}:
                        direction = "🚪 KIRISH"
                    elif label in {"chiqish", "out", "exit", "leave"}:
                        direction = "🚷 CHIQISH"
                    else:
                        direction = "❓ NOMAʼLUM"

                    msg = (
                        f"<b>{direction}</b>\n\n"
                        f"👤 <b>Ism:</b> {employee.name}\n"
                        f"🆔 <b>Employee №:</b> {employee.employee_no}\n"
                        f"🕒 <b>Vaqt:</b> {event.time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"📍 <b>Qurilma:</b> {device.name}"
                    )

                    image_bytes = None
                    picture_url = raw.get("pictureURL") or raw.get("faceURL")

                    if picture_url and device.username and device.password:
                        image_bytes = download_image(picture_url, device)

                    channels = TelegramChannel.objects.filter(user=device.user)
                    for channel in channels:
                        send_telegram(
                            chat_id=channel.chat_id,
                            text=msg,
                            image_bytes=image_bytes
                        )

                    event.sent_to_telegram = True
                    event.save(update_fields=["sent_to_telegram"])
                    last_time = event.time
                    set_last_event_time(last_time)

            except Exception as e:
                self.stderr.write(f"❌ ERROR: {e}")

            time.sleep(5)
