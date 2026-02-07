from concurrent.futures import ThreadPoolExecutor, as_completed

from person.models import Employee
from person.utils import download_face_from_url


class EmployeeService:

    @staticmethod
    def sync_from_hikvision(device, hk_users):
        device_employees = Employee.objects.filter(device=device)
        db_ids = set(device_employees.values_list("employee_no", flat=True))
        hk_ids = {u.get("employeeNo") for u in hk_users if u.get("employeeNo")}
        to_delete = db_ids - hk_ids
        Employee.objects.filter(device=device, employee_no__in=to_delete).delete()

        added = 0
        download_tasks = []

        for u in hk_users:
            emp_no = u.get("employeeNo")
            if not emp_no:
                continue

            emp_obj, created = Employee.objects.update_or_create(
                device=device,
                employee_no=emp_no,
                defaults={
                    "name": u.get("name"),
                    "door_right": u.get("doorRight"),
                    "user_type": u.get("userType"),
                    "raw_json": u,
                    "face_url": u.get("faceURL"),
                }
            )

            if created:
                added += 1

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
                        emp_obj.face_image.save(f"{device.ip}_{emp_obj.employee_no}.jpg", img, save=True, )
                except Exception:
                    pass

        return {
            "added": added,
            "deleted": len(to_delete),
            "device_ip": device.ip,
        }
