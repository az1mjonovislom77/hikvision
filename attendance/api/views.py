from datetime import date
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from attendance.selectors.selectors import get_user_branch
from attendance.services.attendance import AttendanceService


class AbsentEmployeesView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Attendance'],
        parameters=[
            OpenApiParameter(name="date", type=str, description="Kiritilmasa bugungi kun olinadi", required=False),
            OpenApiParameter(name="branch_id", type=int, description="Branch ID (majburiy)", required=True)
        ]
    )
    def get(self, request):
        q_date = request.GET.get("date")
        branch_id = request.GET.get("branch_id")

        if not branch_id:
            return Response({"error": "branch_id majburiy"}, status=400)

        try:
            target_date = date.fromisoformat(q_date) if q_date else date.today()
        except ValueError:
            return Response({"error": "Noto'g'ri sana formati. YYYY-MM-DD ko'rinishida yuboring"}, status=400)

        if target_date > date.today():
            return Response({
                "date": target_date,
                "total": 0,
                "employees": [],
                "message": "Hali kelmagan sana"
            })

        branch = get_user_branch(branch_id=branch_id, user=request.user)

        if not branch:
            return Response({"error": "Branch topilmadi yoki sizga tegishli emas"}, status=400)

        AttendanceService.create_missing_absent_records(branch=branch, target_date=target_date)
        return Response(AttendanceService.absent_records_payload(target_date=target_date))

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

        try:
            parsed_date = date.fromisoformat(q_date)
        except ValueError:
            return Response({"error": "Noto'g'ri sana formati. YYYY-MM-DD ko'rinishida yuboring"}, status=400)

        payload = AttendanceService.update_daily_status(
            employee_id=employee_id,
            target_date=parsed_date,
            status_value=status_value,
            comment=comment,
        )
        return Response(payload)


class MonthlyAttendanceReportView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Attendance'],
        parameters=[
            OpenApiParameter(name="branch_id", type=int, required=True, description="Branch ID (majburiy)"),
            OpenApiParameter(name="employee_id", type=int, required=False, description="Faqat bitta xodim uchun"),
            OpenApiParameter(name="year", type=int, required=True, description="Hisobot yili"),
            OpenApiParameter(name="month", type=int, required=True, description="Hisobot oyi"),
        ]
    )
    def get(self, request):
        branch_id = request.GET.get("branch_id")
        if not branch_id:
            return Response({"error": "branch_id majburiy"}, status=400)

        try:
            year = int(request.GET.get("year"))
            month = int(request.GET.get("month"))
        except (TypeError, ValueError):
            return Response({"error": "year va month to'g'ri son bo'lishi kerak"}, status=400)
        employee_id = request.GET.get("employee_id")

        branch = get_user_branch(branch_id=branch_id, user=request.user)
        if not branch:
            return Response({"error": "Branch topilmadi yoki sizga tegishli emas"}, status=400)

        return Response(AttendanceService.monthly_report_payload(
            branch=branch,
            employee_id=employee_id,
            year=year,
            month=month,
        ))
