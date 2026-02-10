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
        return fetch_face_events([device], since)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker, d) for d in devices]

        for f in as_completed(futures):
            total_saved += f.result()

    return total_saved
