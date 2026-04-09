import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.db import transaction

from event.utils.fetch_employee import fetch_all_employees
from person.models import Employee
from person.utils import download_face_from_url

logger = logging.getLogger(__name__)


class EmployeeService:

    @staticmethod
    def sync_from_hikvision(device, hk_users=None):
        try:
            if hk_users is None:
                hk_users = fetch_all_employees(device)
        except Exception:
            logger.exception(f"[{device.ip}] Employee fetch error")
            return {"added": 0, "deleted": 0, "device_ip": device.ip}

        if not hk_users:
            logger.warning(f"[{device.ip}] API bo‘sh → sync skip")
            return {"added": 0, "deleted": 0, "device_ip": device.ip}

        device_employees = Employee.objects.filter(device=device).only(
            "id", "employee_no", "name", "door_right",
            "user_type", "raw_json", "face_url"
        )

        employee_map = {
            e.employee_no: e for e in device_employees if e.employee_no
        }

        db_ids = set(employee_map.keys())

        hk_ids = {
            u.get("employeeNo")
            for u in hk_users
            if u.get("employeeNo") not in [None, "", "0"]
        }
        should_delete = True

        if not hk_ids:
            logger.warning(f"[{device.ip}] hk_ids empty → delete skip")
            should_delete = False

        elif len(hk_ids) < len(db_ids) * 0.5:
            logger.warning(
                f"[{device.ip}] Kam user ({len(hk_ids)} vs {len(db_ids)}) → delete skip"
            )
            should_delete = False

        if should_delete and len(hk_ids) >= len(db_ids):
            to_delete = db_ids - hk_ids
            if to_delete:
                Employee.objects.filter(device=device, employee_no__in=to_delete).delete()
        else:
            to_delete = set()

        added = 0
        download_tasks = []

        with transaction.atomic():

            for u in hk_users:
                emp_no = u.get("employeeNo")

                if emp_no in [None, "", "0"]:
                    continue

                defaults = {
                    "name": u.get("name"),
                    "door_right": u.get("doorRight"),
                    "user_type": u.get("userType"),
                    "raw_json": u,
                    "face_url": u.get("faceURL"),
                }

                if emp_no in employee_map:
                    emp_obj = employee_map[emp_no]

                    changed = False
                    for k, v in defaults.items():
                        if getattr(emp_obj, k) != v:
                            setattr(emp_obj, k, v)
                            changed = True

                    if changed:
                        emp_obj.save()

                else:
                    emp_obj = Employee.objects.create(
                        device=device,
                        employee_no=emp_no,
                        **defaults
                    )
                    employee_map[emp_no] = emp_obj
                    added += 1

                face_url = u.get("faceURL")
                if face_url:
                    download_tasks.append((emp_obj.id, face_url))

        # 🔥 THREAD SAFE IMAGE DOWNLOAD
        def worker(face_url):
            return download_face_from_url(face_url)

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_map = {
                executor.submit(worker, face_url): emp_id
                for emp_id, face_url in download_tasks
            }

            for future in as_completed(future_map):
                emp_id = future_map[future]

                try:
                    img = future.result()
                    if not img:
                        continue

                    emp_obj = Employee.objects.filter(id=emp_id).first()
                    if not emp_obj:
                        continue

                    emp_obj.face_image.save(
                        f"{device.ip}_{emp_obj.employee_no}.jpg",
                        img,
                        save=False
                    )
                    emp_obj.save(update_fields=["face_image"])

                except Exception:
                    logger.exception(f"[{device.ip}] Image save error")

        return {
            "added": added,
            "deleted": len(to_delete),
            "device_ip": device.ip,
        }
