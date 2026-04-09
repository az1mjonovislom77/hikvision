import logging
from event.utils.fetch_employee import fetch_all_employees
from person.models import Employee
from person.utils import download_face_from_url
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class EmployeeService:

    @staticmethod
    def sync_from_hikvision(device, hk_users=None):
        if hk_users is None:
            hk_users = fetch_all_employees(device)

        device_employees = Employee.objects.filter(device=device).only(
            "id", "employee_no", "name", "door_right", "user_type", "raw_json", "face_url")

        employee_map = {e.employee_no: e for e in device_employees}

        db_ids = set(employee_map.keys())
        hk_ids = {u.get("employeeNo") for u in hk_users if u.get("employeeNo")}


        added = 0
        download_tasks = []

        for u in hk_users:
            emp_no = u.get("employeeNo")
            if not emp_no:
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

                emp_obj.save(update_fields=list(defaults.keys()))

            else:
                emp_obj = Employee.objects.create(device=device, employee_no=emp_no, **defaults)
                added += 1
                employee_map[emp_no] = emp_obj

            face_url = u.get("faceURL")
            if face_url:
                download_tasks.append((emp_obj, face_url))

        def worker(face_url):
            return download_face_from_url(face_url)

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_map = {
                executor.submit(worker, face_url): emp_obj
                for emp_obj, face_url in download_tasks
            }

            for future in as_completed(future_map):
                emp_obj = future_map[future]
                try:
                    img = future.result()
                    if img:
                        emp_obj.face_image.save(f"{device.ip}_{emp_obj.employee_no}.jpg", img, save=True)
                except Exception:
                    logger.exception("Employee fetch failed")

        return {
            "added": added,
            "deleted": 0,
            "device_ip": device.ip,
        }
