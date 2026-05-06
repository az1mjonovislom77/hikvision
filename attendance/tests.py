from calendar import monthrange
from datetime import date, datetime, time
from django.test import TestCase
from django.utils.timezone import make_aware
from rest_framework.test import APIRequestFactory, force_authenticate
from attendance.models import AttendanceDaily
from attendance.utils import count_workdays_in_month, is_employee_workday
from attendance.api.views import MonthlyAttendanceReportView
from day.models import DayOff, Shift, WorkDay
from event.models import AccessEvent
from person.models import Employee
from user.models import User
from utils.models import Branch, Devices


class AttendanceCalculationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone_number="998901234567", password="pass")
        self.device = Devices.objects.create(
            user=self.user,
            name="Device",
            ip="127.0.0.1",
            username="admin",
            password="admin",
            status=Devices.Status.ACTIVE,
        )
        self.branch = Branch.objects.create(user=self.user, name="Branch", device=self.device)
        self.workday = WorkDay.objects.create(
            user=self.user,
            name="Weekdays",
            days=["mon", "tue", "wed", "thu", "fri"],
        )
        self.shift = Shift.objects.create(
            user=self.user,
            name="Office",
            start_time=time(9, 0),
            end_time=time(18, 0),
            approved_late_min=0,
        )

    def create_employee(self, **kwargs):
        defaults = {
            "device": self.device,
            "employee_no": "1",
            "name": "Employee",
            "salary": 2200,
            "shift": self.shift,
            "work_day": self.workday,
            "branch": self.branch,
        }
        defaults.update(kwargs)
        return Employee.objects.create(**defaults)

    def mark_other_workdays_as_excused(self, employee, *, year, month, except_day):
        for day_num in range(1, monthrange(year, month)[1] + 1):
            day = date(year, month, day_num)
            if day == except_day:
                continue
            if is_employee_workday(self.workday, None, day):
                AttendanceDaily.objects.create(employee=employee, date=day, status="sbk")

    def create_access_event(self, employee, serial_no, event_time):
        return AccessEvent.objects.create(
            employee=employee,
            major=5,
            minor=75,
            major_name="major",
            minor_name="minor",
            name=employee.name,
            employee_no=employee.employee_no,
            picture_url="",
            raw_json={},
            device=self.device,
            serial_no=serial_no,
            time=make_aware(event_time),
        )

    def get_monthly_report(self, employee, *, year, month):
        request = APIRequestFactory().get(
            "/attendance/report/monthly/",
            {"branch_id": self.branch.id, "year": year, "month": month, "employee_id": employee.id},
        )
        force_authenticate(request, user=self.user)
        return MonthlyAttendanceReportView.as_view()(request)

    def test_day_off_weekday_codes_are_excluded_from_workdays(self):
        day_off = DayOff.objects.create(user=self.user, name="Mondays off", days=["mon"])

        self.assertFalse(is_employee_workday(self.workday, day_off, datetime(2026, 3, 2).date()))
        self.assertEqual(count_workdays_in_month(self.workday, day_off, 2026, 3), 17)

    def test_absence_fine_save_is_idempotent(self):
        employee = self.create_employee(salary=2200)
        expected_fine = round(employee.salary / count_workdays_in_month(self.workday, None, 2026, 3), 2)

        attendance = AttendanceDaily.objects.create(employee=employee, date=date(2026, 3, 3), status="szk")
        employee.refresh_from_db()
        self.assertAlmostEqual(employee.fine, expected_fine)

        attendance.comment = "updated"
        attendance.save()
        employee.refresh_from_db()
        self.assertAlmostEqual(employee.fine, expected_fine)

        attendance.status = "sbk"
        attendance.save()
        employee.refresh_from_db()
        self.assertEqual(employee.fine, 0)

    def test_monthly_report_does_not_apply_penalties_when_fine_disabled(self):
        employee = self.create_employee(employee_no="2", is_fine=False)
        self.create_access_event(employee, "in", datetime(2026, 3, 3, 9, 0))
        self.create_access_event(employee, "out", datetime(2026, 3, 3, 12, 0))

        response = self.get_monthly_report(employee, year=2026, month=3)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][0]["shift_start_time"], "09:00")
        self.assertEqual(response.data["results"][0]["shift_end_time"], "18:00")
        self.assertEqual(response.data["results"][0]["total_penalty"], 0)
        self.assertEqual(response.data["results"][0]["total_undertime"], "6:00")

    def test_monthly_report_penalty_adds_late_arrival_and_early_leave(self):
        employee = self.create_employee(employee_no="3", is_fine=True)
        target_day = date(2026, 3, 3)
        self.mark_other_workdays_as_excused(employee, year=2026, month=3, except_day=target_day)
        self.create_access_event(employee, "in", datetime(2026, 3, 3, 10, 0))
        self.create_access_event(employee, "out", datetime(2026, 3, 3, 17, 0))

        response = self.get_monthly_report(employee, year=2026, month=3)
        result = response.data["results"][0]
        detail = next(item for item in result["details"] if item["date"] == target_day)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(result["total_overtime"], "0:00")
        self.assertEqual(result["total_undertime"], "2:00")
        self.assertEqual(detail["difference"], "-2:00")
        self.assertGreater(detail["penalty"], 0)
        self.assertEqual(detail["bonus"], 0)

    def test_monthly_report_late_arrival_and_late_departure_are_separate(self):
        employee = self.create_employee(employee_no="4", is_fine=True)
        target_day = date(2026, 3, 3)
        self.mark_other_workdays_as_excused(employee, year=2026, month=3, except_day=target_day)
        self.create_access_event(employee, "in", datetime(2026, 3, 3, 10, 0))
        self.create_access_event(employee, "out", datetime(2026, 3, 3, 19, 0))

        response = self.get_monthly_report(employee, year=2026, month=3)
        result = response.data["results"][0]
        detail = next(item for item in result["details"] if item["date"] == target_day)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(result["total_overtime"], "1:00")
        self.assertEqual(result["total_undertime"], "1:00")
        self.assertEqual(result["net_adjustment"], 0)
        self.assertEqual(detail["difference"], "0:00")
        self.assertAlmostEqual(detail["bonus"], detail["penalty"])
