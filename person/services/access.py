from django.utils.timezone import localtime, make_aware
from datetime import datetime
from django.db.models import Prefetch
from event.models import AccessEvent
from utils.models import Branch
from person.models import Employee
from person.utils import get_first_last_events, format_late, UZ_TZ


class DailyAccessService:

    @staticmethod
    def get_employees(user, branch_id=None):

        event_prefetch = Prefetch(
            "device__events", queryset=AccessEvent.objects.order_by("time"), to_attr="prefetched_events"
        )

        if user.is_staff or user.role == user.UserRoles.SUPERADMIN:
            employees = (Employee.objects
                         .select_related("shift", "device")
                         .prefetch_related(event_prefetch).all())
        else:
            branch_qs = Branch.objects.filter(user=user)
            if branch_id:
                branch_qs = branch_qs.filter(id=branch_id)

            branch = branch_qs.select_related("device").first()
            employees = (
                Employee.objects
                .select_related("shift", "device")
                .prefetch_related(event_prefetch)
                .filter(device=branch.device)
                if branch and branch.device
                else Employee.objects.none()
            )

        return employees

    @staticmethod
    def build_employee_data(emp, date_obj, request):
        first, last = get_first_last_events(emp, date_obj)
        late_minutes = 0

        if emp.shift and first:
            shift_start = emp.shift.start_time
            first_time = localtime(first.time).time()
            shift_minutes = shift_start.hour * 60 + shift_start.minute
            first_minutes = first_time.hour * 60 + first_time.minute
            raw_late = first_minutes - shift_minutes
            approved = emp.shift.approved_late_min or 0

            if raw_late > approved:
                late_minutes = raw_late

        return {
            "first": first,
            "last": last,
            "data": {
                "employee_id": emp.id,
                "employee_no": emp.employee_no,
                "name": emp.name,
                "position": emp.position,
                "kirish": localtime(first.time) if first else None,
                "chiqish": localtime(last.time) if last else None,
                "late": format_late(late_minutes),
                "face": request.build_absolute_uri(emp.face_image.url) if emp.face_image else None
            }, "late_minutes": late_minutes}

    @staticmethod
    def build_excel_row(emp, date_obj):
        first, last = get_first_last_events(emp, date_obj)
        kirish = first.time.astimezone(UZ_TZ).strftime("%H:%M:%S") if first else ""
        chiqish = last.time.astimezone(UZ_TZ).strftime("%H:%M:%S") if last else ""

        late_text = ""

        if emp.shift and first:
            shift_start = make_aware(datetime.combine(date_obj, emp.shift.start_time), UZ_TZ)
            if first.time > shift_start:
                diff = int((first.time - shift_start).total_seconds() / 60)
                late_text = format_late(diff)

        shift_start = emp.shift.start_time.strftime("%H:%M") if emp.shift else ""

        return [emp.employee_no, emp.name, kirish, chiqish, late_text, shift_start]
