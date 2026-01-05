from datetime import date
from calendar import monthrange
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from attendance.models import AttendanceDaily
from person.models import Employee
from drf_spectacular.utils import extend_schema, OpenApiParameter


class AbsentEmployeesView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Attendance'],
        parameters=[
            OpenApiParameter(
                name="date",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Kun (YYYY-MM-DD). Kiritilmasa — bugungi kun olinadi",
                required=False,
            ),
        ]
    )
    def get(self, request):
        q_date = request.GET.get("date")
        target_date = date.fromisoformat(q_date) if q_date else date.today()

        records = AttendanceDaily.objects.filter(date=target_date).exclude(status="present")

        result = [
            {
                "employee_id": r.employee.id,
                "employee_name": r.employee.name,
                "status_label": r.get_status_display(),
                "comment": r.comment,
                "date": r.date,
            }
            for r in records
        ]

        return Response({
            "date": target_date,
            "total": len(result),
            "employees": result
        })


class MonthlyAttendanceReportView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Attendance'],
        parameters=[
            OpenApiParameter(
                name="employee_id",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Faqat bitta xodim uchun",
            ),
            OpenApiParameter(
                name="year",
                type=int,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Hisobot yili (masalan 2025)",
            ),
            OpenApiParameter(
                name="month",
                type=int,
                location=OpenApiParameter.QUERY,
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
