from person.models import Employee
from person.utils import download_face_from_url


class EmployeeService:

    @staticmethod
    def sync_from_hikvision(hk_users):
        db_users = Employee.objects.all()
        db_ids = set(db_users.values_list("employee_no", flat=True))
        hk_ids = {u.get("employeeNo") for u in hk_users}

        to_delete = db_ids - hk_ids
        Employee.objects.filter(employee_no__in=to_delete).delete()

        to_add = hk_ids - db_ids
        added = 0

        for u in hk_users:
            employees_no = u.get("employeeNo")
            if employees_no not in to_add:
                continue

            person, _ = Employee.objects.update_or_create(
                employee_no=employees_no,
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
                    person.face_image.save(f"{employees_no}.jpg", img, save=True)

            added += 1

        return {"added": added, "deleted": len(to_delete)}
