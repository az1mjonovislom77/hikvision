from django.core.cache import cache

KEY = "last_event_time"


def _key(device_id):
    return f"{KEY}:{device_id}"


def get_last_event_time(device_id):
    return cache.get(_key(device_id))


def set_last_event_time(device_id, dt):
    cache.set(_key(device_id), dt, None)
