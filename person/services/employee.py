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

            if u.get("faceURL"):
                img = download_face_from_url(u["faceURL"])
                if img:
                    emp_obj.face_image.save(f"{device.ip}_{emp_no}.jpg", img, save=True)

            if created:
                added += 1

        return {"added": added, "deleted": len(to_delete), "device_ip": device.ip, }
