import logging
import requests
from datetime import timedelta
from event.models import AccessEvent
from requests.auth import HTTPDigestAuth
from event.utils.wrappers import fetch

logger = logging.getLogger(__name__)


class EventSyncService:
    last_sync_time = None

    @staticmethod
    def get_device_event_limit(device):
        url = f"http://{device.ip}/ISAPI/ContentMgmt/Storage"

        try:
            r = requests.get(url, auth=HTTPDigestAuth(device.username, device.password), timeout=8)
            data = r.json()
            storage = data.get("CMStorage", [])

            if isinstance(storage, dict):
                storage = [storage]

            for s in storage:
                if s.get("type") == "EVENT":
                    return int(s.get("capacity", 0))

        except Exception as e:
            logger.error(f"{device.ip} limit error: {e}")

        return 0

    @staticmethod
    def get_device_event_count(device):
        url = f"http://{device.ip}/ISAPI/AccessControl/AcsEventTotal"

        try:
            r = requests.get(url, auth=HTTPDigestAuth(device.username, device.password), timeout=8)
            return int(r.json().get("AcsEventTotal", {}).get("total", 0))

        except Exception as e:
            logger.warning("AcsEventTotal o‘qilmadi: device_id=%s ip=%s: %s", device.id, device.ip, e)
            return 0

    @staticmethod
    def auto_clean_if_needed(device):
        limit = EventSyncService.get_device_event_limit(device)
        if limit <= 0:
            return

        used = EventSyncService.get_device_event_count(device)
        threshold = int(limit * 0.95)

        if used >= threshold:
            logger.warning(f"Device {device.ip} → event limit {used}/{limit} → AUTO CLEAN!")

            url = f"http://{device.ip}/ISAPI/AccessControl/AcsEvent?format=json"
            payload = {"AcsEventCond": {"deleteAll": True}}

            try:
                r = requests.put(url, json=payload, auth=HTTPDigestAuth(device.username, device.password), timeout=10)
                if r.status_code == 200:
                    logger.warning(f"Device {device.ip} eski eventlar o‘chirildi")
                else:
                    logger.error(f"{device.ip} delete failed: {r.text}")
            except Exception as e:
                logger.error(f"{device.ip} delete error: {e}")

    @staticmethod
    def sync_events(devices, full=False):
        """
        full=False: faqat DB dagi eng so‘nggi yozuvdan keyingi eventlar (incremental).
        full=True: startTime yuborilmaydi — qurilmadagi buffergacha bo‘lgan barcha mavjud
        yozuvlar so‘raladi (get_or_create takrorlarni olib tashlaydi).
        """
        device_since_map = {}

        for device in devices:
            if full:
                device_since_map[device.id] = None
            else:
                latest = AccessEvent.objects.filter(device=device, major=5, minor=75).order_by("-time").first()

                if latest:
                    device_since_map[device.id] = latest.time - timedelta(seconds=5)
                else:
                    device_since_map[device.id] = None

        logger.info(
            "EventSyncService.sync_events: full=%s qurilmalar=%s | since_map=%s",
            full,
            [d.id for d in devices],
            {k: (v.isoformat() if v else None) for k, v in device_since_map.items()},
        )
        total = fetch(devices=devices, since_map=device_since_map)
        logger.info("EventSyncService.sync_events tugadi: jami_yangi=%s", total)
        return total

    @staticmethod
    def get_events_queryset():
        return AccessEvent.objects.filter(major=5, minor=75).order_by("-time")
