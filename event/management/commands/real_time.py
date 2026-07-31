import logging
import time

from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.utils import timezone

from event.models import AccessEvent
from event.services.event_state import get_last_event_time, set_last_event_time
from event.utils.wrappers import fetch
from utils.models import Devices, TelegramChannel
from utils.telegram.telegram import download_image, send_telegram
from utils.telegram.telegram_updates import sync_channels_from_updates

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Realtime Hikvision events → Telegram channel"

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Realtime event listener started")
        last_times = {}
        consecutive_errors = 0

        while True:
            try:
                close_old_connections()
                sync_channels_from_updates()
                devices = list(Devices.objects.all())

                for device in devices:
                    if device.id not in last_times:
                        last_time = get_last_event_time(device.id)
                        if last_time is None:
                            last_event = AccessEvent.objects.filter(device=device).order_by("-time").first()
                            last_time = last_event.time if last_event else timezone.now()
                        last_times[device.id] = last_time

                since_map = {d.id: last_times[d.id] for d in devices}
                fetch(devices=devices, since_map=since_map)

                for device in devices:
                    try:
                        self._process_device_events(device, last_times)
                    except Exception:
                        logger.exception("Device events failed: device_id=%s", device.id)

                consecutive_errors = 0

            except Exception:
                consecutive_errors += 1
                logger.exception("MAIN LOOP ERROR (ketma-ket %s-marta)", consecutive_errors)

            time.sleep(min(5 * 2**consecutive_errors, 300) if consecutive_errors else 5)

    def _process_device_events(self, device, last_times):
        events = (
            AccessEvent.objects.filter(device=device, time__gt=last_times[device.id], sent_to_telegram=False)
            .select_related("employee", "device", "device__user")
            .order_by("time")
        )

        channels = list(TelegramChannel.objects.filter(device=device, resolved_id__isnull=False))

        for event in events:
            employee = event.employee

            if not employee or not device.user:
                event.sent_to_telegram = True
                event.save(update_fields=["sent_to_telegram"])
                continue

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

            msg = (
                f"<b>{direction}</b>\n\n"
                f"👤 <b>Ism:</b> {employee.name}\n"
                f"🆔 <b>Employee №:</b> {employee.employee_no}\n"
                f"🕒 <b>Vaqt:</b> {local_time:%Y-%m-%d %H:%M:%S}\n"
                f"📍 <b>Qurilma:</b> {device.name}"
            )

            picture_url = raw.get("pictureURL") or raw.get("faceURL")

            image_bytes = None
            if picture_url and device.username and device.password:
                image_bytes = download_image(picture_url, device)

            if not channels:
                logger.warning(
                    "No resolved telegram channel for device_id=%s (%s) — event %s not sent",
                    device.id,
                    device.name,
                    event.id,
                )

            sent_any = False
            for channel in channels:
                try:
                    send_telegram(chat_id=channel.resolved_id, text=msg, image_bytes=image_bytes)
                    sent_any = True
                    time.sleep(0.3)
                except Exception:
                    logger.exception("Telegram send failed: %s", channel.resolved_id)

            if channels and not sent_any:
                logger.error("Event %s: all channel sends failed, will retry", event.id)
                break

            event.sent_to_telegram = True
            event.save(update_fields=["sent_to_telegram"])

            last_times[device.id] = event.time
            set_last_event_time(device.id, event.time)
