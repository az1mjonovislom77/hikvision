import hashlib
import json
import logging
import time
from datetime import date, datetime, timedelta
from uuid import uuid4

import requests
from django.core.cache import cache
from django.utils import timezone as django_timezone
from django.utils.dateparse import parse_date, parse_datetime
from requests.auth import HTTPDigestAuth

from event.models import AccessEvent
from event.utils.events_name import major_name, minor_name
from person.models import Employee
from person.utils import UZ_TZ, normalize_employee_no

logger = logging.getLogger(__name__)


def _coerce_datetime(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        parsed = parse_datetime(value)
        if parsed is None:
            parsed_date = parse_date(value)
            if parsed_date is None:
                return None
            parsed = datetime.combine(parsed_date, datetime.min.time())
        value = parsed
    elif isinstance(value, date) and not isinstance(value, datetime):
        value = datetime.combine(value, datetime.min.time())
    elif not isinstance(value, datetime):
        return None
    if django_timezone.is_naive(value):
        value = django_timezone.make_aware(value, UZ_TZ)
    return value.astimezone(UZ_TZ)


def _hikvision_time_str(value, legacy=False):
    dt = _coerce_datetime(value)
    if dt is None:
        return None
    dt = dt.replace(microsecond=0)
    if legacy:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return dt.isoformat()


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
        device_saved = 0
        device_seen = 0
        skipped_older = 0
        skipped_invalid_time = 0
        skipped_existing = 0
        unresolved_employee = 0
        since = None
        if since_map:
            raw_since = since_map.get(device.id)
            since = _coerce_datetime(raw_since)
            if raw_since is not None and since is None:
                logger.warning(
                    "event fetch since unparseable, syncing without startTime: device_id=%s raw_since=%r",
                    device.id,
                    raw_since,
                )

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
            url = f"http://{device.ip}/ISAPI/AccessControl/AcsEvent?format=json"
            search_id = uuid4().hex
            employee_exact_map: dict[str, Employee] = {}
            employee_iexact_map: dict[str, Employee] = {}
            for emp in Employee.objects.filter(device=device).only("id", "employee_no"):
                emp_key = normalize_employee_no(emp.employee_no)
                if not emp_key:
                    continue
                employee_exact_map.setdefault(emp_key, emp)
                employee_iexact_map.setdefault(emp_key.lower(), emp)

            time_format_cache_key = f"hikvision:time-format-legacy:{device.id}"
            use_legacy_time = bool(cache.get(time_format_cache_key))
            offset = 0
            limit = 100
            max_pages = 200
            logger.info(
                "event fetch started: device_id=%s ip=%s since=%s search_id=%s max_pages=%s limit=%s forced_minor=75",
                device.id,
                device.ip,
                since.isoformat() if since else None,
                search_id,
                max_pages,
                limit,
            )
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
                    payload["AcsEventCond"]["startTime"] = _hikvision_time_str(since, legacy=use_legacy_time)
                    payload["AcsEventCond"]["endTime"] = _hikvision_time_str(
                        django_timezone.now() + timedelta(days=1), legacy=use_legacy_time
                    )

                try:
                    logger.info(
                        "event fetch request: device_id=%s page=%s offset=%s payload=%s",
                        device.id,
                        page_idx + 1,
                        offset,
                        payload["AcsEventCond"],
                    )
                    r = requests.post(
                        url,
                        json=payload,
                        auth=HTTPDigestAuth(device.username, device.password),
                        headers={"Content-Type": "application/json"},
                        timeout=15,
                    )
                    if r.status_code != 200:
                        if since and not use_legacy_time and r.status_code == 400 and "badJsonContent" in r.text:
                            use_legacy_time = True
                            cache.set(time_format_cache_key, "1", timeout=7 * 24 * 3600)
                            logger.warning(
                                "AcsEvent rejected ISO time format, retrying with legacy format: device_id=%s ip=%s body=%s",
                                device.id,
                                device.ip,
                                r.text[:300],
                            )
                            continue
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
                logger.info(
                    "event fetch response: device_id=%s page=%s status=%s forced_minor=75 events_count=%s totalMatches=%s numOfMatches=%s",
                    device.id,
                    page_idx + 1,
                    r.status_code,
                    len(events),
                    access.get("totalMatches"),
                    access.get("numOfMatches"),
                )

                if not events:
                    logger.info(
                        "event fetch stopped: device_id=%s reason=empty_page page=%s offset=%s forced_minor=75",
                        device.id,
                        page_idx + 1,
                        offset,
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

                    t = UZ_TZ.localize(t) if t.tzinfo is None else t.astimezone(UZ_TZ)

                    if since and t < since:
                        skipped_older += 1
                        continue

                    serial_no = _event_serial_no(device, ev)
                    employee_no = normalize_employee_no(ev.get("employeeNoString") or ev.get("employeeNo"))
                    if employee_no:
                        employee = employee_exact_map.get(employee_no) or employee_iexact_map.get(employee_no.lower())
                    else:
                        employee = None
                    event_major = int(ev.get("major") or 5)
                    event_minor = int(ev.get("minor") or 75)
                    if employee is None and employee_no:
                        unresolved_employee += 1

                    try:
                        _obj, created = AccessEvent.objects.get_or_create(
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
                            },
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
                    "event fetch page summary: device_id=%s page=%s forced_minor=75 seen=%s saved=%s skipped_existing=%s skipped_older=%s unresolved_employee=%s",
                    device.id,
                    page_idx + 1,
                    device_seen,
                    device_saved,
                    skipped_existing,
                    skipped_older,
                    unresolved_employee,
                )

                offset += len(events)

                if len(events) < limit:
                    logger.info(
                        "event fetch stopped: device_id=%s reason=last_page page=%s events_count=%s limit=%s forced_minor=75",
                        device.id,
                        page_idx + 1,
                        len(events),
                        limit,
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
