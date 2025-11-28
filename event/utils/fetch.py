import requests
from django.utils.dateparse import parse_datetime
from event.models import AccessEvent
from event.utils.events_name import major_name, minor_name


def fetch_history_events():
    url = "http://192.168.0.68/ISAPI/AccessControl/AcsEvent?format=json"
    auth = ("admin", "Ats@amaar442")

    payload = {
        "AcsEventCond": {
            "searchID": "300",
            "searchResultPosition": 0,
            "maxResults": 500,
            "major": 0,
            "minor": 0
        }
    }

    r = requests.post(url, json=payload, auth=auth, timeout=5)
    data = r.json()

    events = data.get("AcsEvent", {}).get("InfoList", [])

    saved = 0

    for ev in events:
        serial = ev.get("serialNo")

        if not serial:
            continue

        if AccessEvent.objects.filter(serial_no=serial).exists():
            continue

        AccessEvent.objects.create(
            serial_no=serial,
            time=parse_datetime(ev.get("time")),
            major=ev.get("major"),
            minor=ev.get("minor"),
            major_name=major_name(ev.get("major")),
            minor_name=minor_name(ev.get("minor")),
            name=ev.get("name"),
            employee_no=ev.get("employeeNoString"),
            picture_url=ev.get("pictureURL"),
            raw_json=ev
        )
        saved += 1

    return saved
