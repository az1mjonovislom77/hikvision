import openpyxl
from io import BytesIO
from django.http import HttpResponse
from django.utils.timezone import localdate, now
from django.utils.dateparse import parse_date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.db.models import Prefetch
from event.models import AccessEvent
from person.models import Employee
from person.services.access import DailyAccessService


def get_request_date(request):
    date_str = request.GET.get("date")
    return parse_date(date_str) if date_str else localdate()


@extend_schema(
    tags=["Employee"],
    parameters=[
        OpenApiParameter(name="date", type=str),
        OpenApiParameter(name="branch_id", type=int),
    ],
)
class DailyAccessListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_obj = get_request_date(request)
        branch_id = request.GET.get("branch_id")
        employees = DailyAccessService.get_employees(request.user, branch_id)
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

        return Response({
            "date": str(date_obj),
            "employees": results,
            "stats": stats
        })


@extend_schema(tags=["DailyExel"], parameters=[OpenApiParameter(name="date", type=str)])
class DailyAccessExcelExport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_str = request.GET.get("date")
        date_obj = parse_date(date_str) if date_str else now().date()

        employees = (
            Employee.objects
            .filter(device__user=request.user)
            .select_related("shift", "device")
            .prefetch_related(Prefetch("device__accessevent_set",
                                       queryset=AccessEvent.objects.order_by("time"),
                                       to_attr="prefetched_events")))

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

            return HttpResponse(
                buffer.getvalue(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f'attachment; filename="daily_{date_obj}.xlsx"'}
            )
