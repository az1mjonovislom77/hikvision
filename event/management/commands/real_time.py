import time
import logging
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db import close_old_connections
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
        logger.info("real_time start: last_time_from_cache=%s", last_time)

        if last_time is None:
            last_event = AccessEvent.objects.order_by("-time").first()
            last_time = last_event.time if last_event else timezone.now()
            logger.info("real_time start: cache empty, fallback last_time=%s", last_time)

        devices = list(Devices.objects.all())
        logger.info("real_time start: devices_count=%s device_ids=%s", len(devices), [d.id for d in devices])

        while True:
            try:
                close_old_connections()
                sync_channels_from_updates()

                since_map = {d.id: last_time for d in devices}
                fetch(devices=devices, since_map=since_map)

                events = (
                    AccessEvent.objects
                    .filter(time__gt=last_time, sent_to_telegram=False)
                    .select_related("employee", "device", "device__user")
                    .order_by("time")
                )

                event_list = list(events)
                logger.info(
                    "real_time telegram query: last_time=%s unsent_count=%s",
                    last_time,
                    len(event_list),
                )

                for event in event_list:
                    employee = event.employee
                    device = event.device

                    if not employee or not device or not device.user:
                        logger.info(
                            "real_time skip event: event_id=%s time=%s reason=no_employee_or_device employee=%s device=%s device_user=%s",
                            event.id,
                            event.time,
                            bool(employee),
                            bool(device),
                            bool(device.user) if device else None,
                        )
                        event.sent_to_telegram = True
                        event.save(update_fields=["sent_to_telegram"])
                        continue

                    raw = event.raw_json or {}

                    label = (
                            raw.get("labelName")
                            or raw.get("label")
                            or raw.get("name")
                            or "").strip().lower()

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

                    logger.info(
                        "real_time dispatch telegram: event_id=%s employee_id=%s device_id=%s time=%s",
                        event.id,
                        employee.id,
                        device.id,
                        event.time,
                    )

                    send_event_to_telegram.delay(event.id, msg, picture_url, device.id)
                    last_time = event.time
                    set_last_event_time(last_time)

            except Exception:
                logger.exception("MAIN LOOP ERROR")
            finally:
                close_old_connections()

            time.sleep(5)
