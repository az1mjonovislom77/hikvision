import requests
import time
from requests.auth import HTTPDigestAuth
from django.utils.dateparse import parse_datetime
from event.models import AccessEvent
from event.utils.events_name import major_name, minor_name
from person.utils import UZ_TZ
from person.models import Employee, EmployeeHistory


def fetch_face_events(devices, since=None):
    saved = 0

    for device in devices:
        url = f"http://{device.ip}/ISAPI/AccessControl/AcsEvent?format=json"

        session = requests.Session()
        session.auth = HTTPDigestAuth(device.username, device.password)
        session.headers.update({"Content-Type": "application/json"})

        search_id = "0"
        offset = 0
        limit = 50

        while True:
            payload = {
                "AcsEventCond": {
                    "searchID": search_id,
                    "searchResultPosition": offset,
                    "maxResults": limit,
                    "major": 5,
                    "minor": 75,
                }
            }

            if since:
                payload["AcsEventCond"]["startTime"] = since.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

            try:
                r = session.post(url, json=payload, timeout=15)
                if r.status_code != 200:
                    break
                data = r.json()
            except Exception:
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

                serial_no = ev.get("serialNo")
                employee_no = ev.get("employeeNoString", "")

                label_name = (ev.get("labelName") or ev.get("label") or ev.get("name") or "")

                employee = None
                if employee_no:
                    employee = Employee.objects.filter(
                        employee_no=employee_no,
                        device=device
                    ).first()

                event_obj, created = AccessEvent.objects.get_or_create(
                    device=device,
                    serial_no=serial_no,
                    defaults={
                        "employee": employee,
                        "time": t,
                        "major": 5,
                        "minor": 75,
                        "major_name": major_name(5),
                        "minor_name": minor_name(75),
                        "label_name": label_name,
                        "name": ev.get("name", ""),
                        "employee_no": employee_no,
                        "picture_url": ev.get("pictureURL") or ev.get("faceURL"),
                        "raw_json": ev,
                    }
                )

                if created and employee:
                    EmployeeHistory.objects.create(employee=employee, event=event_obj, event_time=t)
                    saved += 1

            if status != "MORE" or not events:
                break

            offset += len(events)
            time.sleep(0.2)

    return saved
