import logging

from celery import shared_task

from event.services.event_sync import EventSyncService
from utils.models import Devices

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=10, retry_kwargs={"max_retries": 3})
def sync_events_task(self, device_ids, full=True):
    devices = list(Devices.objects.filter(id__in=device_ids))
    if not devices:
        logger.warning("sync_events_task: device topilmadi ids=%s", device_ids)
        return {"added": 0, "devices": 0, "full": full}

    added = EventSyncService.sync_events(devices, full=full)
    return {"added": added, "devices": len(devices), "full": full}
