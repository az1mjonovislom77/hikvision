import logging
from datetime import timedelta
from event.models import AccessEvent
from event.utils.fetch import fetch_face_events
import requests
from requests.auth import HTTPDigestAuth

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

        except:
            return 0

    @staticmethod
    def auto_clean_if_needed(device):
        limit = EventSyncService.get_device_event_limit(device)
        if limit <= 0:
            return

        used = EventSyncService.get_device_event_count(device)
        threshold = int(limit * 0.95)

        if used >= threshold:
            logger.warning(f"⚠️ Device {device.ip} → event limit {used}/{limit} → AUTO CLEAN!")

            url = f"http://{device.ip}/ISAPI/AccessControl/AcsEvent?format=json"
            payload = {"AcsEventCond": {"deleteAll": True}}

            try:
                r = requests.put(url, json=payload, auth=HTTPDigestAuth(device.username, device.password), timeout=10)
                if r.status_code == 200:
                    logger.warning(f"🧹 Device {device.ip} eski eventlar o‘chirildi")
                else:
                    logger.error(f"{device.ip} delete failed: {r.text}")
            except Exception as e:
                logger.error(f"{device.ip} delete error: {e}")

    @staticmethod
    def sync_events(devices):
        latest = AccessEvent.objects.filter(device__in=devices, major=5, minor=75).order_by("-time").first()
        since_time = None
        if latest:
            since_time = latest.time - timedelta(seconds=5)

        return fetch_face_events(devices=devices, since=since_time)

    @staticmethod
    def get_events_queryset():
        return AccessEvent.objects.filter(major=5, minor=75).order_by("-time")
