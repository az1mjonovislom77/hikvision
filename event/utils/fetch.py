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
from event.utils.events_name import MINOR_NAMES, major_name, minor_name

logger = logging.getLogger(__name__)
SUPPORTED_ACCESS_MINORS = tuple(sorted(MINOR_NAMES.keys()))


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


def _request_events(device, payload, page_idx):
    logger.info(
        "event fetch request: device_id=%s page=%s offset=%s payload=%s",
        device.id,
        page_idx + 1,
        payload["AcsEventCond"].get("searchResultPosition"),
        payload["AcsEventCond"],
    )
    return requests.post(
        f"http://{device.ip}/ISAPI/AccessControl/AcsEvent?format=json",
        json=payload,
        auth=HTTPDigestAuth(device.username, device.password),
        headers={"Content-Type": "application/json"},
        timeout=15
    )


def _iter_query_plans():
    yield None
    for minor in SUPPORTED_ACCESS_MINORS:
        yield minor


def fetch_face_events(devices, since_map=None):
    saved = 0

    for device in devices:
        device_saved = 0
        device_seen = 0
        skipped_older = 0
        skipped_invalid_time = 0
        skipped_existing = 0
        unresolved_employee = 0
        since = None
        if since_map:
            since = since_map.get(device.id)

        lock_key = f"hikvision:event-sync:{device.id}"
        if not cache.add(lock_key, "1", timeout=120):
            logger.warning(
                "event fetch skipped by lock: device_id=%s ip=%s lock_key=%s",
                device.id,
                device.ip,
                lock_key,
            )
            continue

        try:
            logger.info(
                "event fetch started: device_id=%s ip=%s since=%s max_pages=%s limit=%s supported_minors=%s",
                device.id,
                device.ip,
                since.isoformat() if since else None,
                200,
                100,
                SUPPORTED_ACCESS_MINORS,
            )
            require_minor_mode = False
            for forced_minor in _iter_query_plans():
                if forced_minor is None and require_minor_mode:
                    continue
                if forced_minor is not None and not require_minor_mode:
                    break

                search_id = uuid4().hex
                offset = 0
                limit = 100
                max_pages = 200
                logger.info(
                    "event fetch query started: device_id=%s search_id=%s forced_minor=%s",
                    device.id,
                    search_id,
                    forced_minor,
                )

                for page_idx in range(max_pages):
                    payload = {
                        "AcsEventCond": {
                            "searchID": search_id,
                            "searchResultPosition": offset,
                            "maxResults": limit,
                            "major": 5,
                        }
                    }
                    if forced_minor is not None:
                        payload["AcsEventCond"]["minor"] = forced_minor
                    if since:
                        payload["AcsEventCond"]["startTime"] = _hikvision_start_time_str(since)

                    try:
                        r = _request_events(device, payload, page_idx)
                        if r.status_code != 200:
                            logger.warning(
                                "AcsEvent error: device_id=%s ip=%s status=%s body=%s",
                                device.id,
                                device.ip,
                                r.status_code,
                                r.text[:300],
                            )
                            if forced_minor is None and "does not exist.minor" in r.text:
                                require_minor_mode = True
                                logger.warning(
                                    "event fetch fallback enabled: device_id=%s reason=minor_required minors=%s",
                                    device.id,
                                    SUPPORTED_ACCESS_MINORS,
                                )
                            break

                        data = r.json()

                    except Exception:
                        logger.exception("Device error: %s", device.id)
                        break

                    access = data.get("AcsEvent", {})
                    events = access.get("InfoList", []) or []
                    logger.info(
                        "event fetch response: device_id=%s page=%s status=%s forced_minor=%s events_count=%s totalMatches=%s numOfMatches=%s",
                        device.id,
                        page_idx + 1,
                        r.status_code,
                        forced_minor,
                        len(events),
                        access.get("totalMatches"),
                        access.get("numOfMatches"),
                    )

                    if not events:
                        logger.info(
                            "event fetch stopped: device_id=%s reason=empty_page page=%s offset=%s forced_minor=%s",
                            device.id,
                            page_idx + 1,
                            offset,
                            forced_minor,
                        )
                        break

                    for ev in events:
                        device_seen += 1
                        t = parse_datetime(ev.get("time"))
                        if not t:
                            skipped_invalid_time += 1
                            logger.warning(
                                "event skipped: device_id=%s reason=invalid_time serial=%s raw_time=%s",
                                device.id,
                                ev.get("serialNo"),
                                ev.get("time"),
                            )
                            continue

                        if t.tzinfo is None:
                            t = UZ_TZ.localize(t)
                        else:
                            t = t.astimezone(UZ_TZ)

                        if since and t < since:
                            skipped_older += 1
                            continue

                        serial_no = _event_serial_no(device, ev)
                        employee_no = normalize_employee_no(ev.get("employeeNoString") or ev.get("employeeNo"))
                        employee = _resolve_employee(device, employee_no)
                        event_major = int(ev.get("major") or 5)
                        event_minor = int(ev.get("minor") or forced_minor or 0)
                        if employee is None and employee_no:
                            unresolved_employee += 1

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
                            device_saved += 1
                            logger.info(
                                "event saved: device_id=%s serial=%s major=%s minor=%s employee_no=%s employee_id=%s time=%s",
                                device.id,
                                serial_no,
                                event_major,
                                event_minor,
                                employee_no,
                                getattr(employee, "id", None),
                                t.isoformat(),
                            )
                        else:
                            skipped_existing += 1

                    logger.info(
                        "event fetch page summary: device_id=%s page=%s forced_minor=%s seen=%s saved=%s skipped_existing=%s skipped_older=%s unresolved_employee=%s",
                        device.id,
                        page_idx + 1,
                        forced_minor,
                        device_seen,
                        device_saved,
                        skipped_existing,
                        skipped_older,
                        unresolved_employee,
                    )

                    offset += len(events)

                    if len(events) < limit:
                        logger.info(
                            "event fetch stopped: device_id=%s reason=last_page page=%s events_count=%s limit=%s forced_minor=%s",
                            device.id,
                            page_idx + 1,
                            len(events),
                            limit,
                            forced_minor,
                        )
                        break

                    time.sleep(0.2)
        finally:
            cache.delete(lock_key)
            logger.info(
                "event fetch finished: device_id=%s ip=%s seen=%s saved=%s skipped_existing=%s skipped_older=%s skipped_invalid_time=%s unresolved_employee=%s",
                device.id,
                device.ip,
                device_seen,
                device_saved,
                skipped_existing,
                skipped_older,
                skipped_invalid_time,
                unresolved_employee,
            )

    return saved
