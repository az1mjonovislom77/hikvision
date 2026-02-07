import logging
from event.utils.fetch import fetch_face_events
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


def fetch(devices, since=None):
    total_saved = 0

    def worker(device):
        return fetch_face_events([device], since)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []

        for device in devices:
            futures.append(executor.submit(worker, device))

        for future in as_completed(futures):
            try:
                result = future.result()
                total_saved += result
            except Exception as e:
                logger.exception("Device event fetch failed", exc_info=e)
                continue

    return total_saved
