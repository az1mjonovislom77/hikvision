import logging
from datetime import datetime

import requests
from django.db.models import Max
from requests.auth import HTTPDigestAuth

from event.models import AccessEvent
from event.utils.wrappers import fetch

logger = logging.getLogger(__name__)


class EventSyncService:
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

        except Exception:
            logger.exception("Qurilma event limitini o'qib bo'lmadi: device_id=%s ip=%s", device.id, device.ip)

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
            logger.warning("Device %s → event limit %s/%s → AUTO CLEAN!", device.ip, used, limit)

            url = f"http://{device.ip}/ISAPI/AccessControl/AcsEvent?format=json"
            payload = {"AcsEventCond": {"deleteAll": True}}

            try:
                r = requests.put(url, json=payload, auth=HTTPDigestAuth(device.username, device.password), timeout=10)
                if r.status_code == 200:
                    logger.warning("Device %s eski eventlar o‘chirildi", device.ip)
                else:
                    logger.error("%s delete failed: status=%s", device.ip, r.status_code)
            except Exception:
                logger.exception("Qurilmada eski eventlarni o'chirib bo'lmadi: ip=%s", device.ip)

    @staticmethod
    def sync_events(devices, full=False):
        device_since_map: dict[int, datetime | None] = {}
        device_descriptions = []

        latest_by_device = {}
        if not full:
            latest_by_device = {
                row["device"]: row["latest_time"]
                for row in (
                    AccessEvent.objects.filter(device__in=devices, major=5, minor=75)
                    .values("device")
                    .annotate(latest_time=Max("time"))
                )
            }

        for device in devices:
            since = None if full else latest_by_device.get(device.id)
            device_since_map[device.id] = since
            device_descriptions.append(
                {
                    "id": device.id,
                    "ip": device.ip,
                    "name": device.name,
                    "since": since.isoformat() if since else None,
                }
            )

        logger.info(
            "event sync service started: full=%s devices=%s",
            full,
            device_descriptions,
        )
        total = fetch(devices=devices, since_map=device_since_map)
        logger.info(
            "event sync service finished: full=%s total_saved=%s device_count=%s",
            full,
            total,
            len(device_descriptions),
        )
        return total

    @staticmethod
    def get_events_queryset():
        return AccessEvent.objects.filter(major=5, minor=75).order_by("-time")
