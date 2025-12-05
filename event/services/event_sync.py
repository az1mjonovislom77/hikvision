import logging
from datetime import timedelta, datetime
from django.utils import timezone
from event.models import AccessEvent
from event.utils.fetch import fetch_face_events

logger = logging.getLogger(__name__)


class EventSyncService:
    last_sync_time = None

    @staticmethod
    def sync_events():

        if EventSyncService.last_sync_time:
            diff = timezone.now() - EventSyncService.last_sync_time
            if diff.total_seconds() < 3:
                return 0

        latest = AccessEvent.objects.filter(major=5, minor=75).order_by("-time").first()
        since_time = latest.time - timedelta(seconds=5) if latest else None

        new_count = fetch_face_events(since=since_time)

        if new_count > 0:
            logger.info(f"{new_count} ta yangi event yuklandi")

        EventSyncService.last_sync_time = timezone.now()

        return new_count

    @staticmethod
    def get_events_queryset():
        return AccessEvent.objects.filter(major=5, minor=75).order_by("-time")
