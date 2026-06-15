from datetime import time, date
from django.test import TestCase
from day.models import Shift, WorkDay, DayOff, BreakTime
from attendance.utils import count_workdays_in_month, is_employee_workday
from user.models import User


class ShiftModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone_number="998903000001", password="pass")

    def test_shift_default_approved_late_is_15(self):
        shift = Shift.objects.create(
            user=self.user, name="Morning",
            start_time=time(9, 0), end_time=time(18, 0),
        )
        self.assertEqual(shift.approved_late_min, 15)

    def test_shift_with_break_time(self):
        break_time = BreakTime.objects.create(
            user=self.user, name="Lunch",
            start_time=time(13, 0), end_time=time(14, 0),
        )
        shift = Shift.objects.create(
            user=self.user, name="Office",
            start_time=time(9, 0), end_time=time(18, 0),
            break_time=break_time,
        )
        self.assertEqual(shift.break_time.name, "Lunch")


class WorkDayTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone_number="998903000002", password="pass")
        self.workday = WorkDay.objects.create(
            user=self.user, name="Weekdays",
            days=["mon", "tue", "wed", "thu", "fri"],
        )

    def test_monday_is_workday(self):
        self.assertTrue(is_employee_workday(self.workday, None, date(2026, 6, 1)))

    def test_saturday_is_not_workday(self):
        self.assertFalse(is_employee_workday(self.workday, None, date(2026, 6, 6)))

    def test_count_workdays_june_2026(self):
        count = count_workdays_in_month(self.workday, None, 2026, 6)
        self.assertEqual(count, 22)

    def test_dayoff_excluded_from_workdays(self):
        day_off = DayOff.objects.create(user=self.user, name="Mondays", days=["mon"])
        count = count_workdays_in_month(self.workday, day_off, 2026, 6)
        self.assertEqual(count, 17)

    def test_dayoff_date_not_workday(self):
        day_off = DayOff.objects.create(user=self.user, name="Fridays", days=["fri"])
        self.assertFalse(is_employee_workday(self.workday, day_off, date(2026, 6, 5)))
