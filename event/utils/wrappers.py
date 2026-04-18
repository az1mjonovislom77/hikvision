import logging
from event.utils.fetch import fetch_face_events
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

def fetch(devices, since_map=None):
    total_saved = 0

    def worker(device):
        since = None
        if since_map:
            since = since_map.get(device.id)
        try:
            return fetch_face_events([device], since)
        except Exception:
            logger.exception(
                "fetch_face_events (parallel) xato: device_id=%s ip=%s",
                device.id,
                getattr(device, "ip", None),
            )
            return 0

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker, d) for d in devices]

        for f in as_completed(futures):
            try:
                total_saved += f.result()
            except Exception:
                logger.exception("Parallel fetch future xatosi")

    return total_saved
