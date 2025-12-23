import time
import logging
import requests

from requests.auth import HTTPDigestAuth
from django.utils.dateparse import parse_datetime

from event.models import AccessEvent
from event.utils.events_name import major_name, minor_name
from person.utils import UZ_TZ
from person.models import Employee, EmployeeHistory

logger = logging.getLogger(__name__)


def fetch_face_events(devices, since=None):
    """
    Hikvision ISAPI AccessControl events fetcher
    - TO‘G‘RI startTime format
    - minor filtrsiz (ishonchli)
    - serialNo fallback
    - employeeNo fallback
    - to‘liq debug loglar
    """

    saved = 0

    for device in devices:
        url = f"http://{device.ip}/ISAPI/AccessControl/AcsEvent?format=json"

        session = requests.Session()
        session.auth = HTTPDigestAuth(device.username, device.password)
        session.headers.update({"Content-Type": "application/json"})

        offset = 0
        limit = 50
        search_id = None

        logger.error(f"📡 HIKVISION FETCH START → device={device.ip}")

        while True:
            payload = {
                "AcsEventCond": {
                    "searchResultPosition": offset,
                    "maxResults": limit,
                    "major": 5,   # Access Control
                }
            }

            # 🔑 TO‘G‘RI startTime FORMAT
            if since:
                payload["AcsEventCond"]["startTime"] = since.strftime(
                    "%Y-%m-%dT%H:%M:%S"
                )

            if search_id:
                payload["AcsEventCond"]["searchID"] = search_id

            try:
                r = session.post(url, json=payload, timeout=15)
                logger.error(f"📡 ISAPI STATUS={r.status_code}")

                if r.status_code != 200:
                    logger.error(f"❌ ISAPI ERROR RESPONSE: {r.text}")
                    break

                data = r.json()
            except Exception:
                logger.exception("❌ ISAPI REQUEST FAILED")
                break

            access = data.get("AcsEvent", {})
            events = access.get("InfoList") or []
            status = access.get("responseStatusStrg")

            if access.get("searchID"):
                search_id = access["searchID"]

            logger.error(
                f"📥 ISAPI EVENTS RECEIVED = {len(events)} "
                f"status={status}"
            )

            if not events:
                break

            for ev in events:
                # ⏱ TIME
                t = parse_datetime(ev.get("time"))
                if not t:
                    continue

                if t.tzinfo is None:
                    t = UZ_TZ.localize(t)
                else:
                    t = t.astimezone(UZ_TZ)

                if since and t <= since:
                    continue

                # 🔑 SERIAL NO (fallback bilan)
                serial_no = (
                    ev.get("serialNo")
                    or ev.get("eventId")
                    or f"{device.id}-{int(t.timestamp())}"
                )

                # 🔑 EMPLOYEE NO (fallback bilan)
                employee_no = (
                    ev.get("employeeNoString")
                    or ev.get("employeeNo")
                    or ev.get("personId")
                    or ""
                )

                label_name = (
                    ev.get("labelName")
                    or ev.get("label")
                    or ev.get("name")
                    or ""
                )

                # 👤 EMPLOYEE
                employee = None
                if employee_no:
                    employee = Employee.objects.filter(
                        employee_no=employee_no,
                        device=device
                    ).first()

                # 🧠 EVENT CREATE
                event_obj, created = AccessEvent.objects.get_or_create(
                    device=device,
                    serial_no=serial_no,
                    defaults={
                        "employee": employee,
                        "time": t,
                        "major": ev.get("major", 5),
                        "minor": ev.get("minor", 0),
                        "major_name": major_name(ev.get("major", 5)),
                        "minor_name": minor_name(ev.get("minor", 0)),
                        "label_name": label_name,
                        "name": ev.get("name", ""),
                        "employee_no": employee_no,
                        "picture_url": ev.get("pictureURL") or ev.get("faceURL"),
                        "raw_json": ev,
                        "sent_to_telegram": False,
                    }
                )

                if created:
                    saved += 1
                    logger.error(
                        f"✅ EVENT SAVED id={event_obj.id} "
                        f"time={t} employee={employee_no}"
                    )

                    if employee:
                        EmployeeHistory.objects.create(
                            employee=employee,
                            event=event_obj,
                            event_time=t
                        )

            if status != "MORE":
                break

            offset += len(events)
            time.sleep(0.2)

        logger.error(
            f"📡 HIKVISION FETCH END → device={device.ip}, saved={saved}"
        )

    return saved
