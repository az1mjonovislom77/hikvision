from datetime import date, datetime
from calendar import monthrange
from django.utils.timezone import make_aware, now
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from attendance.models import AttendanceDaily
from event.models import AccessEvent
from person.models import Employee
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status

from utils.utils.constants import WEEKDAY_CODE_MAP


class AbsentEmployeesView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Attendance'],
        parameters=[
            OpenApiParameter(
                name="date",
                type=str,
                description="Kun (YYYY-MM-DD). Kiritilmasa — bugungi kun olinadi",
                required=False,
            )
        ]
    )
    def get(self, request):
        q_date = request.GET.get("date")
        target_date = date.fromisoformat(q_date) if q_date else date.today()

        current_dt = now()

        employees = Employee.objects.filter(device__user=request.user).distinct()

        for emp in employees:

            if not emp.shift or not emp.shift.start_time or not emp.shift.end_time:
                continue

            if not emp.work_day:
                continue

            day_code = WEEKDAY_CODE_MAP[target_date.weekday()]

            if not getattr(emp.work_day, day_code, False):
                continue

            shift_end = make_aware(datetime.combine(target_date, emp.shift.end_time))

            if current_dt < shift_end:
                continue

            has_event = AccessEvent.objects.filter(employee=emp, time__date=target_date, major=5, minor=75).exists()

            if has_event:
                continue

            AttendanceDaily.objects.get_or_create(
                employee=emp,
                date=target_date,
                defaults={
                    "status": "szk",
                    "comment": "Auto: ish kuni, smena tugadi, kirish eventi yo‘q"
                }
            )

        records = AttendanceDaily.objects.filter(date=target_date, status__in=["sbk", "szk"])

        result = [
            {
                "employee_id": r.employee.id,
                "employee_name": r.employee.name,
                "status": r.status,
                "status_label": r.get_status_display(),
                "comment": r.comment,
                "fine": r.fine_amount,
                "date": r.date
            }
            for r in records
        ]

        return Response({
            "date": target_date,
            "total": len(result),
            "employees": result
        })

    @extend_schema(
        tags=['Attendance'],
        request={
            "application/json": {
                "example": {
                    "employee_id": 5,
                    "date": "2025-02-03",
                    "status": "sbk",
                    "comment": "Kasallik varaqasi"
                }
            }
        }
    )
    def post(self, request):
        employee_id = request.data.get("employee_id")
        q_date = request.data.get("date")
        status_value = request.data.get("status")
        comment = request.data.get("comment")

        if not (employee_id and q_date and status_value):
            return Response({"detail": "employee_id, date va status majburiy"}, status=status.HTTP_400_BAD_REQUEST)

        target_date = date.fromisoformat(q_date)
        employee = Employee.objects.get(id=employee_id)

        obj, created = AttendanceDaily.objects.update_or_create(
            employee=employee,
            date=target_date,
            defaults={
                "status": status_value,
                "comment": comment
            }
        )

        return Response({
            "created": created,
            "employee_id": employee.id,
            "employee_name": employee.name,
            "date": obj.date,
            "status": obj.status,
            "status_label": obj.get_status_display(),
            "fine_amount": obj.fine_amount
        })


class MonthlyAttendanceReportView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Attendance'],
        parameters=[
            OpenApiParameter(
                name="employee_id",
                type=int,
                required=False,
                description="Faqat bitta xodim uchun",
            ),
            OpenApiParameter(
                name="year",
                type=int,
                required=True,
                description="Hisobot yili (masalan 2025)",
            ),
            OpenApiParameter(
                name="month",
                type=int,
                required=True,
                description="Hisobot oyi (1–12)",
            ),
        ],
    )
    def get(self, request):
        year = int(request.GET.get("year"))
        month = int(request.GET.get("month"))
        employee_id = request.GET.get("employee_id")

        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])
        if employee_id:
            employees = Employee.objects.filter(id=employee_id)
        else:
            employees = Employee.objects.filter(device__user=request.user).distinct()

        reports = []

        for emp in employees:
            records = AttendanceDaily.objects.filter(employee=emp, date__gte=start_date, date__lte=end_date)

            report = {
                "employee_id": emp.id,
                "employee_name": emp.name,
                "year": year,
                "month": month,

                "present": records.filter(status="present").count(),
                "absent_excused": records.filter(status="absent_excused").count(),
                "absent_unexcused": records.filter(status="absent_unexcused").count(),

                "total_fine": round(sum(r.fine_amount for r in records if r.fine_amount), 2),

                "details": [
                    {
                        "date": r.date,
                        "status": r.status,
                        "status_label": r.get_status_display(),
                        "comment": r.comment,
                        "fine": r.fine_amount,
                    }
                    for r in records.order_by("date")
                ]
            }

            reports.append(report)

        return Response({
            "year": year,
            "month": month,
            "count": len(reports),
            "results": reports
        })
