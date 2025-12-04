import pytz
import requests
from django.core.files.base import ContentFile
from requests.auth import HTTPDigestAuth
from decouple import config
from event.models import AccessEvent
from person.models import Employee

UZ_TZ = pytz.timezone("Asia/Shanghai")

HIKVISION_IP = config("HIKVISION_IP")
HIKVISION_USER = config("HIKVISION_USER")
HIKVISION_PASS = config("HIKVISION_PASS")


def download_face_from_url(url):
    try:
        r = requests.get(url, auth=HTTPDigestAuth(HIKVISION_USER, HIKVISION_PASS), timeout=10)
        if r.status_code == 200:
            return ContentFile(r.content)
        return None
    except:
        return None


def fix_hikvision_time(begin_dt, end_dt):
    if begin_dt.tzinfo: begin_dt = begin_dt.replace(tzinfo=None)
    if end_dt.tzinfo: end_dt = end_dt.replace(tzinfo=None)

    begin = begin_dt.strftime("%Y-%m-%dT%H:%M:%S")
    end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=0)
    end = end_dt.strftime("%Y-%m-%dT%H:%M:%S")

    return begin, end


def get_next_employee_no():
    url = f"http://{HIKVISION_IP}/ISAPI/AccessControl/UserInfo/Search?format=json"
    payload = {
        "UserInfoSearchCond": {
            "searchID": "1",
            "searchResultPosition": 0,
            "maxResults": 300
        }
    }

    res = requests.post(url, json=payload, auth=HTTPDigestAuth(HIKVISION_USER, HIKVISION_PASS), timeout=10).json()
    hk_users = res.get("UserInfoSearch", {}).get("UserInfo", [])
    hk_ids = set()

    for u in hk_users:
        emp = u.get("employeeNo")
        if emp and emp.isdigit():
            hk_ids.add(int(emp))

    db_ids = set(int(e) for e in Employee.objects.values_list("employee_no", flat=True) if str(e).isdigit())
    all_ids = hk_ids | db_ids
    next_id = max(all_ids) + 1 if all_ids else 1

    while next_id in all_ids:
        next_id += 1

    return str(next_id)


def format_late(minutes):
    if minutes is None:
        return None
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}:{mins:02d}"


def get_first_last_events(emp_no, date_obj, label_in="Kirish", label_out="Chiqish"):
    first_entry = AccessEvent.objects.filter(
        employee_no=emp_no,
        raw_json__label=label_in,
        time__date=date_obj
    ).order_by("time").first()

    last_exit = AccessEvent.objects.filter(
        employee_no=emp_no,
        raw_json__label=label_out,
        time__date=date_obj
    ).order_by("-time").first()

    return first_entry, last_exit
