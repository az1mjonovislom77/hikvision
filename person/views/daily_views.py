import openpyxl
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.utils.timezone import now, make_aware
from django.utils.dateparse import parse_date
from datetime import datetime
from person.models import Employee
from person.utils import get_first_last_events, format_late, UZ_TZ


@extend_schema(tags=["Employee"], parameters=[OpenApiParameter(name="date", type=str)])
class DailyAccessListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_str = request.GET.get("date")
        date_obj = parse_date(date_str) if date_str else now().date()

        user = request.user

        if user.UserRoles.SUPERADMIN or user.is_staff:
            employees = Employee.objects.all()
        else:
            employees = Employee.objects.filter(device__user=user)

        results = []
        stats = {"total": employees.count(), "came": 0, "late": 0, "absent": 0}

        for emp in employees:
            first, last = get_first_last_events(emp.employee_no, date_obj)

            if first:
                stats["came"] += 1
            else:
                stats["absent"] += 1

            late_minutes = 0
            if emp.shift and first:
                shift_start = make_aware(datetime.combine(date_obj, emp.shift.start_time), UZ_TZ)
                if first.time > shift_start:
                    stats["late"] += 1
                    late_minutes = int((first.time - shift_start).total_seconds() / 60)

            results.append({
                "employee_id": emp.id,
                "employee_no": emp.employee_no,
                "name": emp.name,
                "kirish": first.time.astimezone(UZ_TZ) if first else None,
                "chiqish": last.time.astimezone(UZ_TZ) if last else None,
                "late": format_late(late_minutes),
                "face": request.build_absolute_uri(emp.face_image.url) if emp.face_image else None
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
            first, last = get_first_last_events(emp.employee_no, date_obj)
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

        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="daily_{date_obj}.xlsx"'
        wb.save(response)
        return response
