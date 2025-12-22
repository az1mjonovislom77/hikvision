import time
from django.core.management.base import BaseCommand
from django.utils import timezone

from event.services.event_state import get_last_event_time, set_last_event_time
from event.services.event_sync import fetch_face_events
from event.models import AccessEvent

from utils.models import TelegramChannel, Devices
from utils.telegram import send_telegram, download_image, resolve_chat_id


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
                # 1️⃣ Device’lardan eventlarni tortib olish
                devices = Devices.objects.all()
                fetch_face_events(devices=devices, since=last_time)

                # 2️⃣ Yangi eventlar
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

                    # 3️⃣ Rasmni yuklash
                    image_bytes = None
                    picture_url = raw.get("pictureURL") or raw.get("faceURL")

                    if picture_url and device.username and device.password:
                        image_bytes = download_image(picture_url, device)

                    # 4️⃣ Telegram kanallar
                    channels = TelegramChannel.objects.filter(user=device.user)

                    for channel in channels:
                        try:
                            # 🔑 AGAR RESOLVED YO‘Q BO‘LSA — AVTOMATIK ANIQLAYDI
                            if not channel.resolved_id:
                                channel.resolved_id = resolve_chat_id(channel.chat_id)
                                channel.save(update_fields=["resolved_id"])

                            send_telegram(
                                chat_id=channel.resolved_id,
                                text=msg,
                                image_bytes=image_bytes
                            )

                        except Exception as tg_err:
                            self.stderr.write(
                                f"❌ Telegram error ({channel.chat_id}): {tg_err}"
                            )

                    # 5️⃣ Eventni yakunlash
                    event.sent_to_telegram = True
                    event.save(update_fields=["sent_to_telegram"])

                    last_time = event.time
                    set_last_event_time(last_time)

            except Exception as e:
                self.stderr.write(f"❌ LOOP ERROR: {e}")

            time.sleep(5)
