from datetime import date
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from attendance.models import AttendanceDaily
from attendance.tasks.mark_attendance import mark_daily_attendance
from event.models import AccessEvent
from person.models import Employee
from user.models import User
from utils.models import Devices, Branch


class MarkAttendanceTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone_number="998904000001", password="pass")
        self.device = Devices.objects.create(
            user=self.user, name="D", ip="10.0.0.3",
            username="admin", password="admin", status=Devices.Status.ACTIVE,
        )
        self.emp_present = Employee.objects.create(
            device=self.device, employee_no="P1", name="Present Employee"
        )
        self.emp_absent = Employee.objects.create(
            device=self.device, employee_no="A1", name="Absent Employee"
        )

    def test_present_employee_marked_present(self):
        target = date(2026, 6, 10)
        AccessEvent.objects.create(
            employee=self.emp_present, serial_no="s1",
            time="2026-06-10T09:00:00+05:00", major=5, minor=75,
            major_name="m", minor_name="n", name="P1", employee_no="P1",
            picture_url="", raw_json={}, device=self.device, label_name="KIRISH",
        )
        mark_daily_attendance(target_date_str=str(target))
        rec = AttendanceDaily.objects.get(employee=self.emp_present, date=target)
        self.assertEqual(rec.status, "present")

    def test_absent_employee_marked_absent(self):
        target = date(2026, 6, 10)
        mark_daily_attendance(target_date_str=str(target))
        rec = AttendanceDaily.objects.get(employee=self.emp_absent, date=target)
        self.assertEqual(rec.status, "absent_unexcused")

    def test_task_is_idempotent(self):
        target = date(2026, 6, 11)
        mark_daily_attendance(target_date_str=str(target))
        mark_daily_attendance(target_date_str=str(target))
        count = AttendanceDaily.objects.filter(employee=self.emp_absent, date=target).count()
        self.assertEqual(count, 1)


@override_settings(SECURE_SSL_REDIRECT=False)
class AttendanceAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(phone_number="998904000002", password="pass")
        self.device = Devices.objects.create(
            user=self.user, name="D2", ip="10.0.0.4",
            username="admin", password="admin", status=Devices.Status.ACTIVE,
        )
        self.branch = Branch.objects.create(user=self.user, name="B1", device=self.device)
        self.client.force_authenticate(user=self.user)

    def test_absent_view_requires_branch_id(self):
        response = self.client.get("/attendance/absent/")
        self.assertEqual(response.status_code, 400)

    def test_absent_view_invalid_date_returns_400(self):
        response = self.client.get(
            f"/attendance/absent/?branch_id={self.branch.id}&date=not-a-date"
        )
        self.assertEqual(response.status_code, 400)

    def test_monthly_report_invalid_year_returns_400(self):
        response = self.client.get(
            f"/attendance/report/monthly/?branch_id={self.branch.id}&year=abc&month=1"
        )
        self.assertEqual(response.status_code, 400)
