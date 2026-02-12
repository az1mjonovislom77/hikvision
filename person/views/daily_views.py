import openpyxl
from io import BytesIO
from datetime import datetime
from utils.models import Branch
from person.models import Employee
from django.http import HttpResponse
from rest_framework.views import APIView
from django.utils.timezone import localdate
from rest_framework.response import Response
from django.utils.dateparse import parse_date
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now, make_aware, localtime
from drf_spectacular.utils import extend_schema, OpenApiParameter
from person.utils import get_first_last_events, format_late, UZ_TZ


@extend_schema(
    tags=["Employee"],
    parameters=[
        OpenApiParameter(name="date", type=str),
        OpenApiParameter(name="branch_id", type=int),
    ]
)
class DailyAccessListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_str = request.GET.get("date")
        branch_id = request.GET.get("branch_id")

        date_obj = parse_date(date_str) if date_str else localdate()

        user = request.user

        if user.is_staff or user.role == user.UserRoles.SUPERADMIN:
            employees = Employee.objects.all()
        else:
            branch_qs = Branch.objects.filter(user=user)
            if branch_id:
                branch_qs = branch_qs.filter(id=branch_id)

            branch = branch_qs.select_related("device").first()
            employees = (
                Employee.objects.filter(device=branch.device)
                if branch and branch.device
                else Employee.objects.none()
            )

        results = []
        stats = {"total": employees.count(), "came": 0, "late": 0, "absent": 0}

        for emp in employees:
            first, last = get_first_last_events(emp, date_obj)

            if first:
                stats["came"] += 1
            else:
                stats["absent"] += 1

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
                    stats["late"] += 1

            results.append({
                "employee_id": emp.id,
                "employee_no": emp.employee_no,
                "name": emp.name,
                "position": emp.position,
                "kirish": localtime(first.time) if first else None,
                "chiqish": localtime(last.time) if last else None,
                "late": format_late(late_minutes),
                "face": request.build_absolute_uri(emp.face_image.url) if emp.face_image else None,
            })

        return Response({"date": str(date_obj), "employees": results, "stats": stats})


@extend_schema(tags=["DailyExel"], parameters=[OpenApiParameter(name="date", type=str)])
class DailyAccessExcelExport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_str = request.GET.get("date")
        date_obj = parse_date(date_str) if date_str else now().date()

        employees = Employee.objects.filter(device__user=request.user).select_related("shift")

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"{date_obj}"

        ws.append(["Employee No", "Name", "Kirish", "Chiqish", "Late", "Shift"])

        for emp in employees:
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

            ws.append([emp.employee_no, emp.name, kirish, chiqish, late_text, shift_start])

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        response = HttpResponse(output.getvalue(),
                                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="daily_{date_obj}.xlsx"'
        return response
