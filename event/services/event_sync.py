from datetime import timedelta
from event.models import AccessEvent
from event.utils.fetch import fetch_face_events


class EventSyncService:
    @staticmethod
    def sync_events():
        latest = AccessEvent.objects.filter(major=5, minor=75).order_by('-time').first()
        since_time = latest.time - timedelta(seconds=5) if latest else None
        new_count = fetch_face_events(since=since_time)

        return new_count

    @staticmethod
    def get_events_queryset():
        return AccessEvent.objects.filter(major=5, minor=75).order_by('-time')
