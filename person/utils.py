import base64
import requests
from django.core.files.base import ContentFile
from requests.auth import HTTPDigestAuth

from person.models import Person

HIKVISION_IP = "192.168.0.68"
HIKVISION_USER = "admin"
HIKVISION_PASS = "Ats@amaar442"


def base64_to_image_file(base64_str, filename):
    try:
        if "," in base64_str: base64_str = base64_str.split(",")[1]
        return ContentFile(base64.b64decode(base64_str), name=filename)
    except:
        return None


def get_face_from_device(employee_no):
    url = f"http://{HIKVISION_IP}/ISAPI/AccessControl/UserInfo/FaceData/{employee_no}?format=json"
    try:
        res = requests.get(url, auth=HTTPDigestAuth(HIKVISION_USER, HIKVISION_PASS), timeout=10)
        data = res.json()
        return data.get("FaceDataRecord", {}).get("imageData")
    except:
        return None


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

    db_ids = set(int(e) for e in Person.objects.values_list("employee_no", flat=True) if str(e).isdigit())
    all_ids = hk_ids | db_ids
    next_id = max(all_ids) + 1 if all_ids else 1

    while next_id in all_ids:
        next_id += 1

    return str(next_id)
