from datetime import date, datetime, time

from django.test import TestCase
from django.utils.timezone import make_aware
from rest_framework.test import APIRequestFactory, force_authenticate

from attendance.models import AttendanceDaily
from attendance.utils import count_workdays_in_month, is_employee_workday
from attendance.views import MonthlyAttendanceReportView
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
        event_defaults = {
            "employee": employee,
            "major": 5,
            "minor": 75,
            "major_name": "major",
            "minor_name": "minor",
            "name": employee.name,
            "employee_no": employee.employee_no,
            "picture_url": "",
            "raw_json": {},
            "device": self.device,
        }
        AccessEvent.objects.create(
            serial_no="in",
            time=make_aware(datetime(2026, 3, 3, 9, 0)),
            **event_defaults,
        )
        AccessEvent.objects.create(
            serial_no="out",
            time=make_aware(datetime(2026, 3, 3, 12, 0)),
            **event_defaults,
        )

        request = APIRequestFactory().get(
            "/attendance/report/monthly/",
            {"branch_id": self.branch.id, "year": 2026, "month": 3, "employee_id": employee.id},
        )
        force_authenticate(request, user=self.user)

        response = MonthlyAttendanceReportView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][0]["shift_start_time"], "09:00")
        self.assertEqual(response.data["results"][0]["shift_end_time"], "18:00")
        self.assertEqual(response.data["results"][0]["total_penalty"], 0)
        self.assertEqual(response.data["results"][0]["total_undertime"], "6:00")
