import time
import logging
from django.utils import timezone
from django.core.management.base import BaseCommand
from event.models import AccessEvent
from event.utils.wrappers import fetch
from event.services.event_state import get_last_event_time, set_last_event_time
from utils.models import Devices
from utils.telegram.telegram_updates import sync_channels_from_updates
from utils.tasks import send_event_to_telegram

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Realtime Hikvision events → Telegram channel"

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Realtime event listener started")

        last_time = get_last_event_time()
        if last_time is None:
            last_event = AccessEvent.objects.order_by("-time").first()
            last_time = last_event.time if last_event else timezone.now()

        devices = Devices.objects.all()
        while True:
            try:
                sync_channels_from_updates()

                since_map = {d.id: last_time for d in devices}
                fetch(devices=devices, since_map=since_map)

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

                    direction = (
                        "🚪 KIRISH"
                        if label in {"kirish", "in", "entry", "enter"}
                        else "🚷 CHIQISH"
                        if label in {"chiqish", "out", "exit", "leave"}
                        else "❓ NOMAʼLUM"
                    )

                    local_time = timezone.localtime(event.time)

                    msg = (
                        f"<b>{direction}</b>\n\n"
                        f"👤 <b>Ism:</b> {employee.name}\n"
                        f"🆔 <b>Employee №:</b> {employee.employee_no}\n"
                        f"🕒 <b>Vaqt:</b> {local_time:%Y-%m-%d %H:%M:%S}\n"
                        f"📍 <b>Qurilma:</b> {device.name}"
                    )

                    picture_url = raw.get("pictureURL") or raw.get("faceURL")
                    send_event_to_telegram.delay(event.id, msg, picture_url, device.id)

                    last_time = event.time
                    set_last_event_time(last_time)

            except Exception:
                logger.exception("MAIN LOOP ERROR")

            time.sleep(5)
