from calendar import monthrange
from utils.models import Branch
from rest_framework import status
from person.models import Employee
from event.models import AccessEvent
from rest_framework.views import APIView
from rest_framework.response import Response
from attendance.models import AttendanceDaily
from datetime import date, datetime, timedelta
from django.utils.timezone import make_aware, now
from attendance.utils import count_workdays_in_month, is_employee_workday, minutes_to_hm
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter


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

        target_date = date.fromisoformat(q_date) if q_date else date.today()

        today = date.today()
        current_dt = now()

        if target_date > today:
            return Response({
                "date": target_date,
                "total": 0,
                "employees": [],
                "message": "Hali kelmagan sana"
            })

        branch = Branch.objects.filter(id=branch_id, user=request.user).first()

        if not branch:
            return Response({"error": "Branch topilmadi yoki sizga tegishli emas"}, status=400)

        employees = Employee.objects.filter(device=branch.device).distinct()

        for emp in employees:

            if not emp.shift or not emp.shift.start_time or not emp.shift.end_time:
                continue

            if not emp.work_day or not emp.work_day.days:
                continue

            if not is_employee_workday(emp.work_day, emp.day_off, target_date):
                continue

            shift_end = make_aware(datetime.combine(target_date, emp.shift.end_time))

            if target_date == today and current_dt < shift_end:
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

        return Response({
            "date": target_date,
            "total": records.count(),
            "employees": [
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
            defaults={"status": status_value, "comment": comment}
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

        year = int(request.GET.get("year"))
        month = int(request.GET.get("month"))
        employee_id = request.GET.get("employee_id")

        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])

        today = date.today()
        current_dt = now()

        branch = Branch.objects.filter(id=branch_id, user=request.user).first()

        if not branch:
            return Response({"error": "Branch topilmadi yoki sizga tegishli emas"}, status=400)

        employees = (Employee.objects.filter(id=employee_id, device=branch.device)
                     if employee_id else
                     Employee.objects.filter(device=branch.device).distinct())

        reports = []

        for emp in employees:

            workdays = count_workdays_in_month(emp.work_day, emp.day_off, year, month)
            day_salary = emp.salary / workdays if workdays else 0

            total_bonus = 0
            total_penalty = 0
            total_overtime = 0
            total_undertime = 0
            worked_minutes = 0
            sbk_count = 0
            szk_count = 0
            details = []

            for day in (start_date + timedelta(days=i)
                        for i in range((end_date - start_date).days + 1)):

                if day > today:
                    continue

                if not emp.shift or not emp.work_day:
                    continue

                if not is_employee_workday(emp.work_day, emp.day_off, day):
                    continue

                shift_end = make_aware(datetime.combine(day, emp.shift.end_time))
                if day == today and current_dt < shift_end:
                    continue

                attendance = AttendanceDaily.objects.filter(employee=emp, date=day).first()
                events = AccessEvent.objects.filter(employee=emp, time__date=day)

                if not events.exists():

                    if attendance and attendance.status == "sbk":
                        sbk_count += 1
                        details.append({
                            "date": day,
                            "status": "sbk",
                            "status_label": "Sababli kelmadi",
                            "worked": "0:00",
                            "difference": "0:00",
                            "penalty": 0
                        })
                    else:
                        szk_count += 1
                        penalty_amount = round(day_salary, 2) if emp.is_fine else 0

                        if total_penalty + penalty_amount > emp.salary:
                            penalty_amount = max(0, emp.salary - total_penalty)

                        total_penalty += penalty_amount

                        details.append({
                            "date": day,
                            "status": "szk",
                            "status_label": "Sababsiz kelmadi",
                            "worked": "0:00",
                            "difference": "0:00",
                            "penalty": penalty_amount
                        })

                    continue

                first_event = events.earliest("time")
                last_event = events.latest("time")

                first_in = first_event.time.time()
                last_out = last_event.time.time()

                shift_start_dt = datetime.combine(day, emp.shift.start_time)
                first_in_dt = datetime.combine(day, first_in)

                late_minutes = int((first_in_dt - shift_start_dt).total_seconds() / 60)
                approved_late = emp.shift.approved_late_min or 0

                if late_minutes <= approved_late:
                    late_minutes = 0

                worked_min = int(
                    (datetime.combine(day, last_out) - datetime.combine(day, first_in)).total_seconds() / 60)

                worked_min -= late_minutes
                worked_minutes += worked_min

                shift_min = int(
                    (datetime.combine(day, emp.shift.end_time) -
                     datetime.combine(day, emp.shift.start_time)
                     ).total_seconds() / 60
                )

                diff = worked_min - shift_min
                minute_salary = day_salary / shift_min
                money = round(diff * minute_salary, 2)

                if diff > 0:
                    total_bonus += money
                    total_overtime += diff
                elif diff < 0 and emp.is_fine:
                    total_penalty += abs(money)
                    total_undertime += abs(diff)
                elif diff < 0:
                    total_undertime += abs(diff)

            reports.append({
                "employee_id": emp.id,
                "employee_name": emp.name,
                "year": year,
                "month": month,
                "sbk_count": sbk_count,
                "szk_count": szk_count,
                "worked_time": minutes_to_hm(worked_minutes),
                "total_overtime": minutes_to_hm(total_overtime),
                "total_undertime": minutes_to_hm(total_undertime),
                "total_bonus": int(round(total_bonus)),
                "total_penalty": int(round(total_penalty)),
                "net_adjustment": int(round(abs(total_bonus - total_penalty))),
                "details": details
            })

        return Response({
            "year": year,
            "month": month,
            "count": len(reports),
            "results": reports
        })
