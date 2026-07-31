import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from event.utils.fetch_employee import fetch_all_employees
from person.models import Employee
from person.utils import download_face_from_url, normalize_employee_no

logger = logging.getLogger(__name__)


class EmployeeService:
    @staticmethod
    def sync_from_hikvision(device, hk_users=None):
        logger.info("sync_from_hikvision started: device=%s", device.ip)

        if hk_users is None:
            hk_users = fetch_all_employees(device)

        logger.info("sync_from_hikvision fetched: device=%s count=%d", device.ip, len(hk_users))

        if not hk_users:
            logger.warning("sync_from_hikvision: empty result from device=%s", device.ip)
            return {
                "added": 0,
                "deleted": 0,
                "device_ip": device.ip,
            }

        device_employees = Employee.objects.filter(device=device).only(
            "id", "employee_no", "name", "door_right", "user_type", "raw_json", "face_url"
        )

        employee_map = {normalize_employee_no(e.employee_no): e for e in device_employees}

        added = 0
        download_tasks = []
        to_update = []
        update_fields = ["name", "door_right", "user_type", "raw_json", "face_url"]

        for u in hk_users:
            emp_no = normalize_employee_no(u.get("employeeNo"))

            if not emp_no:
                logger.warning("sync_from_hikvision: skipping user without employeeNo device=%s", device.ip)
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
                for k, v in defaults.items():
                    setattr(emp_obj, k, v)
                to_update.append(emp_obj)
            else:
                emp_obj = Employee.objects.create(device=device, employee_no=emp_no, **defaults)
                added += 1
                employee_map[emp_no] = emp_obj

            face_url = u.get("faceURL")
            if face_url:
                download_tasks.append((emp_obj, face_url))

        if to_update:
            Employee.objects.bulk_update(to_update, update_fields)

        logger.info(
            "sync_from_hikvision processed: device=%s total=%d added=%d faces=%d",
            device.ip,
            len(hk_users),
            added,
            len(download_tasks),
        )

        def worker(face_url):
            return download_face_from_url(face_url)

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_map = {executor.submit(worker, face_url): emp_obj for emp_obj, face_url in download_tasks}

            for future in as_completed(future_map):
                emp_obj = future_map[future]
                try:
                    img = future.result()
                    if img:
                        emp_obj.face_image.save(
                            f"{device.ip}_{emp_obj.employee_no}.jpg",
                            img,
                            save=True,
                        )
                except Exception:
                    logger.exception("sync_from_hikvision: face save failed employee_no=%s", emp_obj.employee_no)
                time.sleep(0.2)

        logger.info("sync_from_hikvision done: device=%s added=%d", device.ip, added)

        return {
            "added": added,
            "deleted": 0,
            "device_ip": device.ip,
        }
