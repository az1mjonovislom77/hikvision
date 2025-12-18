from django.core.management.base import BaseCommand
import time
from event.services.event_state import get_last_event_time, set_last_event_time
from event.services.event_sync import fetch_face_events
from event.models import AccessEvent
from utils.telegram import send_telegram, download_image


class Command(BaseCommand):
    help = "Realtime Hikvision events → Telegram channel (every 5 sec)"
    sent_serials = set()

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Realtime event listener started")

        last_time = get_last_event_time()

        if last_time is None:
            last_event = AccessEvent.objects.order_by("-time").first()
            if last_event:
                last_time = last_event.time
            else:
                from django.utils import timezone
                last_time = timezone.now()

        while True:
            try:
                fetch_face_events(since=last_time)

                events = AccessEvent.objects.filter(
                    time__gt=last_time,
                    sent_to_telegram=False
                ).select_related("employee", "employee__device").order_by("time")

                for event in events:
                    employee = event.employee
                    device = employee.device if employee else None

                    raw = event.raw_json or {}
                    label = raw.get("label", "")
                    label_normalized = label.strip().lower()

                    kirish_labels = {"kirish", "in", "entry", "enter"}
                    chiqish_labels = {"chiqish", "out", "exit", "leave"}

                    if label_normalized in kirish_labels:
                        direction = "KIRISH"
                    elif label_normalized in chiqish_labels:
                        direction = "CHIQISH"
                    else:
                        direction = "NOMAʼLUM"

                    name = employee.name if employee else "Nomaʼlum"
                    emp_no = employee.employee_no if employee else "-"
                    device_name = device.name if device else "Nomaʼlum"

                    msg = (
                        f"🚪 <b>{direction}</b>\n\n"
                        f"👤 <b>Ism:</b> {name}\n"
                        f"🆔 <b>Employee №:</b> {emp_no}\n"
                        f"🕒 <b>Vaqt:</b> {event.time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"📍 <b>Qurilma:</b> {device_name}"
                    )

                    picture_url = raw.get("pictureURL")

                    image_bytes = None
                    if picture_url and device and device.username and device.password:
                        image_bytes = download_image(picture_url, device)
                    if image_bytes:
                        send_telegram(msg, image_bytes=image_bytes)
                        print("TELEGRAM SENT WITH IMAGE")
                    else:
                        print("NO IMAGE → SKIPPED TELEGRAM")

                    event.sent_to_telegram = True
                    event.save(update_fields=["sent_to_telegram"])
                    last_time = event.time
                    set_last_event_time(last_time)

            except Exception as e:
                self.stderr.write(str(e))

            time.sleep(5)
