import requests
import time
from urllib.parse import urlparse
from requests.auth import HTTPDigestAuth
from django.utils.dateparse import parse_datetime
from event.models import AccessEvent
from event.utils.events_name import major_name, minor_name
from datetime import datetime
from person.utils import UZ_TZ
from person.models import Employee
from utils.models import Devices


def fetch_face_events(since: datetime = None):
    saved = 0
    devices = Devices.objects.all()

    for device in devices:

        url = f"http://{device.ip}/ISAPI/AccessControl/AcsEvent?format=json"
        headers = {"Content-Type": "application/json"}

        search_id = "0"
        offset = 0
        limit = 50

        while True:
            session = requests.Session()
            session.auth = HTTPDigestAuth(device.username, device.password)
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

                if t.tzinfo is None:
                    t = UZ_TZ.localize(t)
                else:
                    t = t.astimezone(UZ_TZ)

                if since and t <= since:
                    continue

                pic_url = ev.get("pictureURL") or ev.get("faceURL")

                event_ip = None
                if pic_url:
                    parsed = urlparse(pic_url)
                    event_ip = parsed.hostname

                local_emp = ev.get("employeeNoString", "")

                employee_obj = None
                if event_ip and local_emp:
                    employee_obj = Employee.objects.filter(
                        employee_no=local_emp,
                        device__ip=event_ip
                    ).first()

                if AccessEvent.objects.filter(serial_no=ev.get("serialNo"), time=t).exists():
                    continue

                AccessEvent.objects.create(
                    employee=employee_obj,
                    serial_no=ev.get("serialNo"),
                    time=t,
                    major=5,
                    minor=75,
                    major_name=major_name(5),
                    minor_name=minor_name(75),
                    name=ev.get("name", ""),
                    employee_no=local_emp,
                    picture_url=pic_url,
                    raw_json=ev
                )

                saved += 1

            if status != "MORE" or len(events) == 0:
                break

            offset += len(events)
            time.sleep(0.2)

    return saved
