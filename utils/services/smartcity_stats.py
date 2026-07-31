from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

from person.models import Employee
from user.models import User


class SmartCityStatsService:
    TIME_FILTERS = {
        "week": 7,
        "3month": 90,
        "6month": 180,
        "year": 365,
    }

    def __init__(self, time_filter: str):
        if time_filter not in self.TIME_FILTERS:
            raise ValueError("Invalid time_filter")

        self.time_filter = time_filter
        self.end_date = timezone.now()
        self.start_date = self.end_date - timedelta(days=self.TIME_FILTERS[time_filter])

    @staticmethod
    def base_employee_queryset():
        return Employee.objects.filter(device__user__role=User.UserRoles.MAHALLA)

    def total_mahallas(self):
        return User.objects.filter(role=User.UserRoles.MAHALLA).count()

    def total_employees(self):
        return self.base_employee_queryset().count()

    def present_employees(self):
        return self.base_employee_queryset().filter(begin_time__range=(self.start_date, self.end_date)).count()

    def absent_employees(self):
        return self.total_employees() - self.present_employees()

    def average_attendance(self):
        total = self.total_employees()
        if total == 0:
            return 0

        percent = (self.present_employees() * 100) / total
        return round(percent, 1)

    def mahalla_statistics(self):
        qs = (
            self.base_employee_queryset()
            .values("device__user__id", "device__user__full_name")
            .annotate(
                total_employees=Count("id"),
                present_employees=Count("id", filter=Q(begin_time__range=(self.start_date, self.end_date))),
            )
        )

        result = []

        for item in qs:
            total = item["total_employees"]
            present = item["present_employees"]
            absent = total - present

            percentage = round((present * 100) / total, 1) if total else 0

            result.append(
                {
                    "id": item["device__user__id"],
                    "mahallaName": item["device__user__full_name"],
                    "totalEmployees": total,
                    "presentEmployees": present,
                    "absentEmployees": absent,
                    "attendancePercentage": percentage,
                }
            )

        return result

    def best_and_worst(self, attendance_data):
        if not attendance_data:
            return None, None

        sorted_data = sorted(attendance_data, key=lambda x: x["attendancePercentage"], reverse=True)

        best = sorted_data[0]
        worst = sorted_data[-1]

        return best, worst

    def build(self):
        attendance_data = self.mahalla_statistics()
        best, worst = self.best_and_worst(attendance_data)

        total = self.total_employees()
        present = self.present_employees()

        return {
            "timeFilter": self.time_filter,
            "summary": {
                "totalMahallas": self.total_mahallas(),
                "totalEmployees": total,
                "presentEmployees": present,
                "absentEmployees": total - present,
                "averageAttendance": round((present * 100) / total, 1) if total else 0,
                "bestAttendanceMahalla": best,
                "worstAttendanceMahalla": worst,
            },
            "attendance": attendance_data,
        }
