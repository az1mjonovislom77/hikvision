import requests
import time
from requests.auth import HTTPDigestAuth
from django.utils.dateparse import parse_datetime
from event.models import AccessEvent
from event.utils.events_name import major_name, minor_name
from datetime import datetime
from decouple import config
import pytz
HIKVISION_IP = config("HIKVISION_IP")
HIKVISION_USER = config("HIKVISION_USER")
HIKVISION_PASS = config("HIKVISION_PASS")
UZ_TZ = pytz.timezone("Asia/Shanghai")

def fetch_face_events(since: datetime = None):
    url = f"http://{HIKVISION_IP}/ISAPI/AccessControl/AcsEvent?format=json"
    headers = {"Content-Type": "application/json"}
    saved = 0
    search_id = "0"
    offset = 0
    limit = 50

    while True:
        session = requests.Session()
        session.auth = HTTPDigestAuth(f"{HIKVISION_USER}", f"{HIKVISION_PASS}")
        session.headers.update(headers)

        payload = {
            "AcsEventCond": {
                "searchID": search_id,
                "searchResultPosition": offset,
                "maxResults": limit,
                "major": 5,
                "minor": 75
            }
        }

        if since:
            payload["AcsEventCond"]["startTime"] = since.strftime("%Y-%m-%d %H:%M:%S")

        try:
            r = session.post(url, json=payload, timeout=15)
            if r.status_code == 401:
                time.sleep(1)
                continue
            if r.status_code != 200:
                break
            data = r.json()
        except:
            break

        acs = data.get("AcsEvent", {})
        events = acs.get("InfoList", []) or []
        status = acs.get("responseStatusStrg", "")

        if acs.get("searchID") and acs["searchID"] != "0":
            search_id = acs["searchID"]

        for ev in events:

            t = parse_datetime(ev.get("time"))
            if not t:
                continue

            # ❗❗❗ Uzbekistan vaqtiga konvert qilish
            if t.tzinfo is None:
                t = UZ_TZ.localize(t)
            else:
                t = t.astimezone(UZ_TZ)

            if since and t <= since:
                continue

            if AccessEvent.objects.filter(serial_no=ev.get("serialNo"), time=t).exists():
                continue

            AccessEvent.objects.create(
                serial_no=ev.get("serialNo"),
                time=t,
                major=5,
                minor=75,
                major_name=major_name(5),
                minor_name=minor_name(75),
                name=ev.get("name", ""),
                employee_no=ev.get("employeeNoString", ""),
                picture_url=ev.get("pictureURL"),
                raw_json=ev
            )
            saved += 1

        if status != "MORE" or len(events) == 0:
            break

        offset += len(events)
        time.sleep(0.3)

    return saved
