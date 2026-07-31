import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.db import close_old_connections, connection

from event.utils.fetch import fetch_face_events

logger = logging.getLogger(__name__)


def fetch(devices, since_map=None):
    total_saved = 0

    def worker(device):
        close_old_connections()
        since = None
        if since_map:
            since = since_map.get(device.id)
        try:
            return fetch_face_events([device], {device.id: since} if since else None)
        except Exception:
            logger.exception(
                "fetch_face_events (parallel) xato: device_id=%s ip=%s",
                device.id,
                getattr(device, "ip", None),
            )
            return 0
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker, d) for d in devices]

        for f in as_completed(futures):
            try:
                total_saved += f.result()
            except Exception:
                logger.exception("Parallel fetch future xatosi")

    return total_saved
