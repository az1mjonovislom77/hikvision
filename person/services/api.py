import time
import uuid
from io import BytesIO
import openpyxl
from user.models import User
from person.models import Employee, EmployeeHistory
from person.selectors.person import (
    empty_employee_history_queryset,
    get_access_events_for_history,
    get_branch_device_queryset,
    get_existing_employee_history_event_ids,
    get_employee_history_for_day,
    get_user_employees_with_events,
    get_target_user,
    get_user_branch,
)
from person.services.access import DailyAccessService
from person.services.employee import EmployeeService
from person.services.hikvision import HikvisionService
from person.utils import fix_hikvision_time, normalize_employee_no


class EmployeeAPIService:
    @staticmethod
    def resolve_branch(*, user, branch_id, user_id=None):
        if user.role == User.UserRoles.SUPERADMIN or user.is_staff:
            if not user_id:
                return None, {"error": "user_id superadmin uchun majburiy"}, 400

            target_user = get_target_user(user_id=user_id)
            if not target_user:
                return None, {"error": "Bunday user topilmadi"}, 404

            return get_user_branch(branch_id=branch_id, user=target_user), None, None

        return get_user_branch(branch_id=branch_id, user=user), None, None

    @staticmethod
    def sync_branch_devices(*, branch):
        devices = get_branch_device_queryset(branch=branch)

        total_stats = {
            "synced_devices": 0,
            "added": 0,
            "deleted": 0,
        }

        for device in devices:
            stats = EmployeeService.sync_from_hikvision(device)

            total_stats["synced_devices"] += 1
            total_stats["added"] += stats["added"]
            total_stats["deleted"] += stats["deleted"]

        return {"success": True, **total_stats}

    @staticmethod
    def create_employee(*, data, device):
        employee_no = uuid.uuid4().hex[:16]
        begin, end = fix_hikvision_time(data["begin_time"], data["end_time"])

        payload = {
            "UserInfo": {
                "employeeNo": employee_no,
                "name": data["name"],
                "userType": data.get("user_type", "normal"),
                "doorRight": data.get("door_right", "1"),
                "Valid": {
                    "enable": True,
                    "beginTime": begin,
                    "endTime": end,
                    "timeType": "local"
                }
            }
        }

        time.sleep(3)
        result = HikvisionService.create_user(device, payload)
        if result.status_code != 200:
            return None, {"error": "Hikvision xatosi", "detail": result.text}, 400

        employee = Employee.objects.create(**data, device=device, employee_no=employee_no)
        return {"status": "created", "employee_no": employee_no, "id": employee.id, "device": device.ip}, None, None

    @staticmethod
    def update_employee(*, employee, serializer):
        data = serializer.validated_data

        name = data.get("name", employee.name)
        user_type = data.get("user_type", employee.user_type)
        door_right = data.get("door_right", employee.door_right)
        begin = data.get("begin_time", employee.begin_time)
        end = data.get("end_time", employee.end_time)

        begin_str, end_str = fix_hikvision_time(begin, end)

        payload = {
            "UserInfo": {
                "employeeNo": employee.employee_no,
                "name": name,
                "userType": user_type,
                "doorRight": door_right,
                "Valid": {
                    "enable": True,
                    "beginTime": begin_str,
                    "endTime": end_str,
                    "timeType": "local"
                }
            }
        }

        result = HikvisionService.update_user(employee.device, payload)
        if result.status_code != 200:
            return {"error": "Update failed", "detail": result.text}, 400

        serializer.save()
        return {"status": "updated"}, None

    @staticmethod
    def delete_employee(*, employee):
        result = HikvisionService.delete_user(employee.device, employee.employee_no)
        if result.status_code != 200:
            return {"error": "Delete failed", "detail": result.text}, 400

        employee.delete()
        return {"status": "deleted"}, None


class EmployeeHistoryService:
    @staticmethod
    def build_queryset(*, user, employee, employee_id, start, end):
        if not employee:
            return empty_employee_history_queryset()

        if not user.role == User.UserRoles.SUPERADMIN and not user.is_staff:
            if employee.device.user != user:
                return empty_employee_history_queryset()

        qs = get_employee_history_for_day(employee_id=employee_id, start=start, end=end)

        if not qs.exists():
            employee_no = normalize_employee_no(employee.employee_no)
            events = list(get_access_events_for_history(
                employee_no=employee_no,
                device=employee.device,
                start=start,
                end=end,
            ))

            existing_event_ids = get_existing_employee_history_event_ids(employee=employee, events=events)
            to_create = []

            for ev in events:
                if ev.id not in existing_event_ids:
                    to_create.append(
                        EmployeeHistory(employee=employee, event=ev, event_time=ev.time, label_name=ev.label_name))

            if to_create:
                EmployeeHistory.objects.bulk_create(to_create)

            qs = get_employee_history_for_day(employee_id=employee_id, start=start, end=end)

        return qs.order_by("-event_time")


class DailyAccessAPIService:
    @staticmethod
    def list_payload(*, user, branch_id, date_obj, request):
        employees = DailyAccessService.get_employees(user, branch_id)
        stats = {"total": employees.count(), "came": 0, "late": 0, "absent": 0}

        results = []

        for emp in employees:
            result = DailyAccessService.build_employee_data(emp, date_obj, request)
            first = result["first"]
            if first:
                stats["came"] += 1
            else:
                stats["absent"] += 1
            if result["late_minutes"]:
                stats["late"] += 1

            results.append(result["data"])

        return {
            "date": str(date_obj),
            "employees": results,
            "stats": stats
        }

    @staticmethod
    def excel_bytes(*, user, date_obj):
        employees = get_user_employees_with_events(user=user)

        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = f"{date_obj}"
        sheet.append(["Employee No", "Name", "Kirish", "Chiqish", "Late", "Shift"])

        for emp in employees:
            row = DailyAccessService.build_excel_row(emp, date_obj)
            sheet.append(row)

        with BytesIO() as buffer:
            workbook.save(buffer)
            buffer.seek(0)
            return buffer.getvalue()
