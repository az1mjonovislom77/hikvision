from django.core.cache import cache

KEY = "last_event_time"


def get_last_event_time():
    return cache.get(KEY)


def set_last_event_time(dt):
    cache.set(KEY, dt, None)
