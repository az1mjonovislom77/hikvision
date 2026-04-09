import time
import logging
from event.utils.fetch_employee import fetch_all_employees
from person.models import Employee
from person.utils import download_face_from_url

logger = logging.getLogger(__name__)


class EmployeeService:

    @staticmethod
    def sync_from_hikvision(device, hk_users=None):
        if hk_users is None:
            hk_users = fetch_all_employees(device)

        logger.warning(f"🚀 SYNC START | device={device.ip} | hk={len(hk_users)}")

        device_employees = Employee.objects.filter(device=device).only(
            "id", "employee_no", "name", "door_right", "user_type", "raw_json", "face_url"
        )

        employee_map = {e.employee_no: e for e in device_employees}

        added = 0

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

                updated = False
                for k, v in defaults.items():
                    if getattr(emp_obj, k) != v:
                        setattr(emp_obj, k, v)
                        updated = True

                if updated:
                    emp_obj.save(update_fields=list(defaults.keys()))

            else:
                emp_obj = Employee.objects.create(
                    device=device,
                    employee_no=emp_no,
                    **defaults
                )
                added += 1
                employee_map[emp_no] = emp_obj

            face_url = u.get("faceURL")
            if face_url:
                try:
                    img = download_face_from_url(face_url)
                    if img:
                        emp_obj.face_image.save(
                            f"{device.ip}_{emp_obj.employee_no}.jpg",
                            img,
                            save=True
                        )
                except Exception:
                    logger.exception("❌ Face download failed")

                time.sleep(0.3)
        time.sleep(3)

        logger.warning(f"✅ SYNC DONE | added={added}")

        return {
            "added": added,
            "deleted": 0,
            "device_ip": device.ip,
        }