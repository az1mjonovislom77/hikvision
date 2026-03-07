from datetime import datetime
from django.utils import timezone
from django.db.models import Count, Q
from person.models import Employee
from user.models import User


class SmartCityDailyStatsService:

    def __init__(self, date, mahalla_id=None):
        self.date = datetime.strptime(date, "%Y-%m-%d").date()
        self.start = timezone.make_aware(datetime.combine(self.date, datetime.min.time()))
        self.end = timezone.make_aware(datetime.combine(self.date, datetime.max.time()))
        self.mahalla_id = mahalla_id

    def base_queryset(self):
        qs = Employee.objects.select_related("device__user", "shift").filter(device__user__role=User.UserRoles.MAHALLA)

        if self.mahalla_id:
            qs = qs.filter(device__user__id=self.mahalla_id)

        return qs

    def employee_detail(self):
        qs = self.base_queryset().select_related("device__user", "shift")

        result = []

        for emp in qs:
            begin = None
            end = None

            if emp.begin_time and self.start <= emp.begin_time <= self.end:
                begin = emp.begin_time
            if emp.end_time and self.start <= emp.end_time <= self.end:
                end = emp.end_time

            status = "ABSENT"

            if begin:

                status = "PRESENT"

                if emp.shift and emp.shift.start_time:
                    if begin.time() > emp.shift.start_time:
                        status = "LATE"
                    else:
                        status = "ON_TIME"

            result.append({
                "employeeId": emp.id,
                "employeeName": emp.name,
                "mahallaId": emp.device.user.id if emp.device and emp.device.user else None,
                "mahallaName": emp.device.user.full_name if emp.device and emp.device.user else None,
                "beginTime": begin,
                "endTime": end,
                "status": status,
            })

        return result

    def mahalla_summary(self):

        qs = (self.base_queryset()
              .values("device__user__id", "device__user__full_name")
              .annotate(total=Count("id"),
                        present=Count("id", filter=Q(begin_time__range=(self.start, self.end)))))

        result = []

        for item in qs:
            total = item["total"]
            present = item["present"]
            absent = total - present

            percentage = round((present * 100) / total, 1) if total else 0

            result.append({
                "mahallaId": item["device__user__id"],
                "mahallaName": item["device__user__full_name"],
                "totalEmployees": total,
                "presentEmployees": present,
                "absentEmployees": absent,
                "attendancePercentage": percentage,
            })

        return result

    def build(self):
        if self.mahalla_id:
            return {"type": "detail", "data": self.employee_detail()}

        return {"type": "summary", "data": self.mahalla_summary()}
