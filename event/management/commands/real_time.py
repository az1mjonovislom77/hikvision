import time
import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from event.services.event_state import get_last_event_time, set_last_event_time
from event.services.event_sync import fetch_face_events
from event.models import AccessEvent

from utils.models import TelegramChannel, Devices
from utils.telegram import send_telegram, download_image
from utils.telegram_updates import sync_channels_from_updates


# 🔥 MUHIM: logger aniq olinadi
logger = logging.getLogger("realtime_events")


class Command(BaseCommand):
    help = "Realtime Hikvision events → Telegram channel"

    def handle(self, *args, **kwargs):
        # Bu print HAR DOIM chiqadi
        self.stdout.write("🚀 Realtime event listener started")

        logger.error("🔥 HANDLE STARTED (LOGGER WORKING)")

        last_time = get_last_event_time()
        if last_time is None:
            last_event = AccessEvent.objects.order_by("-time").first()
            last_time = last_event.time if last_event else timezone.now()

        logger.error(f"⏱ Initial last_time = {last_time}")

        while True:
            try:
                # 🔄 LOOP ISHLAYAPTIMI — ANIQLASH UCHUN
                logger.error("🔄 LOOP TICK")

                # 1️⃣ Telegram update’larni sync qilish
                try:
                    sync_channels_from_updates()
                    logger.error("✅ sync_channels_from_updates OK")
                except Exception:
                    logger.exception("❌ sync_channels_from_updates FAILED")

                # 2️⃣ Device’lar
                devices = Devices.objects.all()
                logger.error(f"📟 Devices count = {devices.count()}")

                # 3️⃣ Hikvision’dan eventlarni olish
                fetch_face_events(devices=devices, since=last_time)
                logger.error("📡 fetch_face_events CALLED")

                # 4️⃣ Yangi eventlar
                events = (
                    AccessEvent.objects
                    .filter(time__gt=last_time, sent_to_telegram=False)
                    .select_related("employee", "device", "device__user")
                    .order_by("time")
                )

                logger.error(f"📥 Events count = {events.count()}")

                for event in events:
                    logger.error(f"➡️ PROCESS EVENT id={event.id}")

                    employee = event.employee
                    device = event.device

                    if not employee or not device or not device.user:
                        logger.error("⚠️ Event skipped (missing employee/device/user)")
                        event.sent_to_telegram = True
                        event.save(update_fields=["sent_to_telegram"])
                        continue

                    # 5️⃣ Direction aniqlash
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
                        f"🕒 <b>Vaqt:</b> {event.time:%Y-%m-%d %H:%M:%S}\n"
                        f"📍 <b>Qurilma:</b> {device.name}"
                    )

                    # 6️⃣ Rasm
                    image_bytes = None
                    picture_url = raw.get("pictureURL") or raw.get("faceURL")

                    if picture_url and device.username and device.password:
                        image_bytes = download_image(picture_url, device)
                        logger.error("🖼 Image downloaded")
                    else:
                        logger.error("🖼 No image")

                    # 7️⃣ TELEGRAM KANALLAR (ENG MUHIM JOY)
                    logger.error(f"🧪 device.user_id = {device.user_id}")

                    all_channels = TelegramChannel.objects.all()
                    logger.error(f"🧪 ALL channels count = {all_channels.count()}")

                    channels = TelegramChannel.objects.filter(
                        user=device.user,
                        resolved_id__isnull=False
                    )

                    logger.error(f"🧪 FILTERED channels count = {channels.count()}")

                    for channel in channels:
                        logger.error(
                            f"📤 TRY SEND → channel_id={channel.id} "
                            f"resolved_id={channel.resolved_id}"
                        )
                        try:
                            send_telegram(
                                chat_id=channel.resolved_id,
                                text=msg,
                                image_bytes=image_bytes
                            )
                            logger.error("✅ TELEGRAM SENT")
                        except Exception:
                            logger.exception("❌ TELEGRAM SEND FAILED")

                    # 8️⃣ Eventni yopish
                    event.sent_to_telegram = True
                    event.save(update_fields=["sent_to_telegram"])

                    last_time = event.time
                    set_last_event_time(last_time)

                    logger.error(f"✅ EVENT DONE id={event.id}")

            except Exception:
                logger.exception("💥 MAIN LOOP ERROR")

            time.sleep(5)
