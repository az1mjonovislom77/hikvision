import hashlib
import json
import logging
import time
from uuid import uuid4
import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import RequestException, Timeout
from django.core.cache import cache
from django.utils import timezone as django_timezone
from person.utils import UZ_TZ
from event.models import AccessEvent
from requests.auth import HTTPDigestAuth
from django.utils.dateparse import parse_datetime
from person.models import Employee, EmployeeHistory
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


def fetch_face_events(devices, since=None):
    saved = 0

    for device in devices:
        lock_key = f"hikvision:event-sync:{device.id}"
        if not cache.add(lock_key, "1", timeout=120):
            continue

        url = f"http://{device.ip}/ISAPI/AccessControl/AcsEvent?format=json"
        search_id = uuid4().hex
        offset = 0
        limit = 100
        max_pages = 500
        pages_done = 0
        saved_this_device = 0
        stop_reason = "ok"

        for page_idx in range(max_pages):
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
                payload["AcsEventCond"]["startTime"] = _hikvision_start_time_str(since)

            try:
                r = requests.post(
                    url, json=payload,
                    auth=HTTPDigestAuth(device.username, device.password),
                    headers={"Content-Type": "application/json"}, timeout=15)

                if r.status_code != 200:
                    logger.warning("HTTP xato: device_id=%s status=%s", device.id, r.status_code, )
                    stop_reason = f"http_{r.status_code}"
                    break

                data = r.json()

            except Timeout:
                logger.warning("Timeout: device_id=%s", device.id)
                stop_reason = "timeout"
                break
            except RequestsConnectionError:
                logger.warning("Connection error: device_id=%s", device.id)
                stop_reason = "connection"
                break
            except RequestException:
                logger.warning("Request error: device_id=%s", device.id)
                stop_reason = "request"
                break
            except Exception:
                logger.exception("Unexpected error: device_id=%s", device.id)
                stop_reason = "unexpected"
                break

            access = data.get("AcsEvent", {})
            events = access.get("InfoList", []) or []

            if not events:
                break

            pages_done += 1

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

                serial_no = _event_serial_no(device, ev)
                employee_no = normalize_employee_no(ev.get("employeeNoString") or ev.get("employeeNo"))
                label_name = ev.get("labelName") or ev.get("label") or ev.get("name") or ""

                employee = _resolve_employee(device, employee_no)

                try:
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
                except Exception:
                    logger.exception("DB error: device_id=%s", device.id)
                    continue

                if created and employee:
                    try:
                        EmployeeHistory.objects.create(employee=employee, event=event_obj, event_time=t)
                    except Exception:
                        logger.exception("History error: device_id=%s", device.id)

                if created:
                    saved += 1
                    saved_this_device += 1

            offset += len(events)

            if len(events) < limit:
                break

            time.sleep(0.2)

        if stop_reason != "ok":
            logger.warning("Stopped: reason=%s device_id=%s", stop_reason, device.id, )

        cache.delete(lock_key)

    return saved
