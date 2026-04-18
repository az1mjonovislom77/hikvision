import hashlib
import json
import logging
import time
from uuid import uuid4
from datetime import timezone as dt_timezone
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
from event.utils.events_name import major_name, minor_name

logger = logging.getLogger(__name__)


def _hikvision_start_time_str(since):
    """
    Hikvision AcsEvent startTime odatda vaqt zonasiz qator — qurilma sozlamasidagi mahalliy vaqt.
    DB dagi aware vaqtni Asia/Tashkent ga o‘girib yuboramiz (settings.TIME_ZONE bilan mos).
    """
    if since is None:
        return None
    if django_timezone.is_naive(since):
        since = django_timezone.make_aware(since, UZ_TZ)
    return since.astimezone(UZ_TZ).strftime("%Y-%m-%d %H:%M:%S")


def _event_serial_no(device, ev):
    """Hikvision serialNo bo‘sh bo‘lsa, bir vaqtdagi turli eventlar bitta qotib qolmasligi uchun barqaror kalit."""
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
            logger.warning(
                "AcsEvent skip: boshqa sync ishlayapti device_id=%s ip=%s",
                device.id,
                device.ip,
            )
            continue

        url = f"http://{device.ip}/ISAPI/AccessControl/AcsEvent?format=json"
        start_local = _hikvision_start_time_str(since)
        since_utc = (
            since.astimezone(dt_timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
            if since
            else None
        )
        logger.info(
            "AcsEvent boshlandi: device_id=%s ip=%s startTime_mahalliy=%s (DB_UTC=%s)",
            device.id,
            device.ip,
            start_local or "(barcha)",
            since_utc or "—",
        )

        session = requests.Session()
        session.auth = HTTPDigestAuth(device.username, device.password)
        session.headers.update({"Content-Type": "application/json"})

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
                r = session.post(url, json=payload, timeout=15)
                if r.status_code != 200:
                    logger.warning(
                        "AcsEvent HTTP xato: device_id=%s ip=%s status=%s offset=%s searchID=%s body=%s",
                        device.id,
                        device.ip,
                        r.status_code,
                        offset,
                        search_id,
                        (r.text or "")[:800],
                    )
                    stop_reason = f"http_{r.status_code}"
                    break
                try:
                    data = r.json()
                except ValueError:
                    logger.warning(
                        "AcsEvent JSON emas: device_id=%s ip=%s offset=%s body=%s",
                        device.id,
                        device.ip,
                        offset,
                        (r.text or "")[:800],
                    )
                    stop_reason = "json_parse"
                    break
            except Timeout as e:
                logger.warning(
                    "AcsEvent timeout (qurilma javob bermadi): device_id=%s ip=%s offset=%s: %s",
                    device.id,
                    device.ip,
                    offset,
                    e,
                )
                stop_reason = "timeout"
                break
            except RequestsConnectionError as e:
                logger.warning(
                    "AcsEvent ulanish yo‘q: device_id=%s ip=%s offset=%s — "
                    "VPS odatda 192.168.* ga bevosita chiqa olmaydi (VPN/tunnel yoki ochiq IP kerak): %s",
                    device.id,
                    device.ip,
                    offset,
                    e,
                )
                stop_reason = "connection"
                break
            except RequestException as e:
                logger.warning(
                    "AcsEvent HTTP kutilmagan xato: device_id=%s ip=%s offset=%s: %s",
                    device.id,
                    device.ip,
                    offset,
                    e,
                )
                stop_reason = "request"
                break
            except Exception:
                logger.exception(
                    "AcsEvent so‘rov (noma’lum) xatosi: device_id=%s ip=%s offset=%s searchID=%s",
                    device.id,
                    device.ip,
                    offset,
                    search_id,
                )
                stop_reason = "unexpected"
                break

            if not isinstance(data, dict):
                logger.error(
                    "AcsEvent JSON kutilmagan format: device_id=%s ip=%s type=%s",
                    device.id,
                    device.ip,
                    type(data).__name__,
                )
                stop_reason = "json_shape"
                break

            access = data.get("AcsEvent", {})
            events = access.get("InfoList", []) or []

            if access.get("searchID") and access["searchID"] != "0":
                search_id = access["searchID"]

            if not events:
                logger.debug(
                    "AcsEvent bo‘sh sahifa, tugadi: device_id=%s ip=%s offset=%s",
                    device.id,
                    device.ip,
                    offset,
                )
                break

            pages_done += 1
            status_raw = access.get("responseStatusStrg") or ""
            logger.debug(
                "AcsEvent sahifa: device_id=%s ip=%s page=%s offset=%s len=%s status=%r searchID=%s",
                device.id,
                device.ip,
                page_idx,
                offset,
                len(events),
                status_raw,
                search_id,
            )

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
                employee_no = ev.get("employeeNoString", "")
                label_name = (
                        ev.get("labelName")
                        or ev.get("label")
                        or ev.get("name")
                        or ""
                )

                employee = None
                if employee_no:
                    employee = Employee.objects.filter(employee_no=employee_no, device=device).first()

                try:
                    event_obj, created = AccessEvent.objects.get_or_create(
                        device=device, serial_no=serial_no,
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
                    logger.exception(
                        "AccessEvent DB xatosi: device_id=%s ip=%s serial_no=%s time=%s employee_no=%s",
                        device.id,
                        device.ip,
                        serial_no,
                        t,
                        employee_no,
                    )
                    continue

                if created and employee:
                    try:
                        EmployeeHistory.objects.create(employee=employee, event=event_obj, event_time=t)
                    except Exception:
                        logger.exception(
                            "EmployeeHistory yaratish xatosi: device_id=%s event_id=%s employee_id=%s",
                            device.id,
                            getattr(event_obj, "id", None),
                            getattr(employee, "id", None),
                        )

                if created:
                    saved += 1
                    saved_this_device += 1

            offset += len(events)
            status = (access.get("responseStatusStrg") or "").upper()
            if len(events) < limit and status != "MORE":
                break
            time.sleep(0.2)
        else:
            stop_reason = "max_pages"
            logger.warning(
                "AcsEvent max_pages (%s) yetildi, boshqa sahifalar bo‘lishi mumkin: device_id=%s ip=%s",
                max_pages,
                device.id,
                device.ip,
            )

        if stop_reason == "ok":
            note = ""
            if pages_done > 0 and saved_this_device == 0:
                note = " | yangi hodisa yo‘q (qurilma javobi DB dagi yozuvlar bilan mos yoki filtr ostida)"
            logger.info(
                "AcsEvent tugadi: device_id=%s ip=%s sahifalar=%s yangi_saqlangan=%s%s",
                device.id,
                device.ip,
                pages_done,
                saved_this_device,
                note,
            )
        else:
            logger.warning(
                "AcsEvent to‘xtatildi: sabab=%s device_id=%s ip=%s sahifalar=%s yangi_saqlangan=%s",
                stop_reason,
                device.id,
                device.ip,
                pages_done,
                saved_this_device,
            )

        cache.delete(lock_key)

    return saved
