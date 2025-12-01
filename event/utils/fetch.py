import requests
import time
from requests.auth import HTTPDigestAuth
from django.utils.dateparse import parse_datetime
from event.models import AccessEvent
from event.utils.events_name import major_name, minor_name


def fetch_face_events():
    url = "http://192.168.0.68/ISAPI/AccessControl/AcsEvent?format=json"
    headers = {"Content-Type": "application/json"}

    saved = 0
    search_id = "0"
    offset = 0
    limit = 50

    print("Face eventlar yuklanmoqda (faqat offset bilan, time filter yo‘q)...")

    while True:
        session = requests.Session()
        session.auth = HTTPDigestAuth("admin", "Ats@amaar442")
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

        try:
            r = session.post(url, json=payload, timeout=15)
            print(f"Offset {offset} → Status: {r.status_code}")

            if r.status_code == 401:
                print("  401 chiqdi → yangi session bilan davom etamiz")
                time.sleep(1)
                continue

            if r.status_code != 200:
                print(f"  Xato {r.status_code}: {r.text[:200]}")
                break

            data = r.json()

        except Exception as e:
            print(f"  Request xatosi: {e}")
            break

        acs = data.get("AcsEvent", {})
        events = acs.get("InfoList", [])
        status = acs.get("responseStatusStrg", "")

        if search_id == "0" and acs.get("searchID") and acs.get("searchID") != "0":
            search_id = acs["searchID"]
            print(f"  Yangi searchID: {search_id}")

        if not events:
            print("  Hech nima kelmedi → tugadi")
            break

        new_in_page = 0
        for ev in events:
            t = parse_datetime(ev.get("time"))
            if not t:
                continue

            if AccessEvent.objects.filter(serial_no=ev.get("serialNo"), time=t).exists():
                continue

            AccessEvent.objects.create(
                serial_no=ev.get("serialNo"),
                time=t,
                major=ev.get("major"),
                minor=ev.get("minor"),
                major_name=major_name(ev.get("major")),
                minor_name=minor_name(ev.get("minor")),
                name=ev.get("name", ""),
                employee_no=ev.get("employeeNoString", ""),
                picture_url=ev.get("pictureURL"),
                raw_json=ev
            )
            saved += 1
            new_in_page += 1

        print(f"  {len(events)} ta keldi → {new_in_page} tasi yangi saqlandi | {status}")

        offset += len(events)

        if status != "MORE":
            print("  Hikvision: hammasi berildi (MORE emas)")
            break

        if offset >= 1000:
            print("  Offset 1000 ga yetdi → qolganlari boshqa usul bilan olinadi")
            break

        time.sleep(0.5)

    total = AccessEvent.objects.filter(major=5, minor=75).count()
    print(f"\nTUGADI!")
    print(f"Yangi qo‘shilgan: {saved} ta")
    print(f"DB’da jami: {total} ta (418 bo‘lishi kerak)")

    return saved
