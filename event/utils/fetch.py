import hashlib
import json
import logging
import time
from uuid import uuid4
import requests
from django.core.cache import cache
from django.utils import timezone as django_timezone
from person.utils import UZ_TZ
from event.models import AccessEvent
from requests.auth import HTTPDigestAuth
from django.utils.dateparse import parse_datetime
from person.models import Employee
from person.utils import normalize_employee_no
from event.utils.events_name import major_name, minor_name

logger = logging.getLogger(__name__)


def _resolve_employee(device, employee_no):
    employee_no = normalize_employee_no(employee_no)
    if not employee_no:
        return None

    employee = Employee.objects.filter(device=device, employee_no=employee_no).first()
    if employee:
        return employee

    return Employee.objects.filter(device=device).filter(employee_no__iexact=employee_no).first()


def _hikvision_start_time_str(since):
    if since is None:
        return None
    if django_timezone.is_naive(since):
        since = django_timezone.make_aware(since, UZ_TZ)
    return since.astimezone(UZ_TZ).strftime("%Y-%m-%d %H:%M:%S")


def _event_serial_no(device, ev):
    sn = ev.get("serialNo")
    if sn is not None and str(sn).strip() != "":
        return str(sn).strip()[:100]
    payload = json.dumps(ev, sort_keys=True, ensure_ascii=False, default=str)
    digest = hashlib.sha256(f"{device.id}:{payload}".encode()).hexdigest()[:40]
    return f"h{digest}"


def fetch_face_events(devices, since_map=None):
    saved = 0

    for device in devices:
        since = None
        if since_map:
            since = since_map.get(device.id)

        lock_key = f"hikvision:event-sync:{device.id}"
        if not cache.add(lock_key, "1", timeout=120):
            continue

        try:
            url = f"http://{device.ip}/ISAPI/AccessControl/AcsEvent?format=json"
            search_id = uuid4().hex
            offset = 0
            limit = 100
            max_pages = 200

            for page_idx in range(max_pages):
                payload = {
                    "AcsEventCond": {
                        "searchID": search_id,
                        "searchResultPosition": offset,
                        "maxResults": limit,
                        "major": 5,
                    }
                }
                if since:
                    payload["AcsEventCond"]["startTime"] = _hikvision_start_time_str(since)

                try:
                    r = requests.post(
                        url,
                        json=payload,
                        auth=HTTPDigestAuth(device.username, device.password),
                        headers={"Content-Type": "application/json"},
                        timeout=15
                    )

                    if r.status_code != 200:
                        logger.warning(
                            "AcsEvent error: device_id=%s ip=%s status=%s body=%s",
                            device.id,
                            device.ip,
                            r.status_code,
                            r.text[:300],
                        )
                        break

                    data = r.json()

                except Exception:
                    logger.exception("Device error: %s", device.id)
                    break

                access = data.get("AcsEvent", {})
                events = access.get("InfoList", []) or []

                if not events:
                    break

                for ev in events:
                    t = parse_datetime(ev.get("time"))
                    if not t:
                        continue

                    if t.tzinfo is None:
                        t = UZ_TZ.localize(t)
                    else:
                        t = t.astimezone(UZ_TZ)

                    if since and t < since:
                        continue

                    serial_no = _event_serial_no(device, ev)
                    employee_no = normalize_employee_no(ev.get("employeeNoString") or ev.get("employeeNo"))
                    employee = _resolve_employee(device, employee_no)
                    event_major = int(ev.get("major") or 5)
                    event_minor = int(ev.get("minor") or 0)

                    try:
                        obj, created = AccessEvent.objects.get_or_create(
                            device=device,
                            serial_no=serial_no,
                            defaults={
                                "employee": employee,
                                "time": t,
                                "major": event_major,
                                "minor": event_minor,
                                "major_name": major_name(event_major),
                                "minor_name": minor_name(event_minor),
                                "employee_no": employee_no,
                                "label_name": ev.get("labelName") or ev.get("label") or "",
                                "name": ev.get("name", ""),
                                "picture_url": ev.get("pictureURL") or ev.get("faceURL") or "",
                                "raw_json": ev,
                            }
                        )
                    except Exception:
                        logger.exception("DB error")
                        continue

                    if created:
                        saved += 1

                offset += len(events)

                if len(events) < limit:
                    break

                time.sleep(0.2)
        finally:
            cache.delete(lock_key)

    return saved
