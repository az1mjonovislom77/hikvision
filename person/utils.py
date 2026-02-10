import pytz
import requests
from utils.models import Devices
from urllib.parse import urlparse
from datetime import datetime, time
from event.models import AccessEvent
from requests.auth import HTTPDigestAuth
from django.utils.timezone import make_aware
from django.core.files.base import ContentFile

UZ_TZ = pytz.timezone("Asia/Tashkent")


def download_face_from_url(url):
    if not url:
        return None

    try:
        parsed = urlparse(url)
        device_ip = parsed.hostname
        if not device_ip:
            return None
        device = Devices.objects.filter(ip=device_ip).first()

        if not device:
            return None

        result = requests.get(url, auth=HTTPDigestAuth(device.username, device.password), timeout=10)

        if result.status_code == 200:
            return ContentFile(result.content)
        return None

    except Exception:
        return None


def fix_hikvision_time(begin_dt, end_dt):
    if begin_dt.tzinfo:
        begin_dt = begin_dt.replace(tzinfo=None)

    if end_dt.tzinfo:
        end_dt = end_dt.replace(tzinfo=None)

    begin = begin_dt.strftime("%Y-%m-%dT%H:%M:%S")
    end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=0)
    end = end_dt.strftime("%Y-%m-%dT%H:%M:%S")

    return begin, end


def format_late(minutes):
    if minutes is None:
        return None
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}:{mins:02d}"


def get_day_range(date_obj):
    start = make_aware(datetime.combine(date_obj, time.min))
    end = make_aware(datetime.combine(date_obj, time.max))
    return start, end


def get_first_last_events(emp_no, date_obj):
    start = make_aware(datetime.combine(date_obj, time.min))
    end = make_aware(datetime.combine(date_obj, time.max))

    qs = AccessEvent.objects.filter(employee_no=emp_no, time__range=(start, end))

    first_entry = qs.filter(label_name__in=["KIRISH", "checkIn", "Kirish", "Keldim"]).order_by("time").first()

    last_exit = qs.filter(label_name__in=["CHIQISH", "checkOut", "Chiqish", "Ketdim"]).order_by("-time").first()

    return first_entry, last_exit
