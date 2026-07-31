from datetime import date, datetime
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils.timezone import make_aware
from rest_framework.test import APIClient

from event.models import AccessEvent
from person.models import Employee
from person.services.hikvision import HikvisionService
from person.utils import fix_hikvision_time, format_late, get_first_last_events, normalize_employee_no
from user.models import User
from utils.models import Branch, Devices


@override_settings(SECURE_SSL_REDIRECT=False)
class EmployeePermissionTests(TestCase):
    client: APIClient

    def setUp(self):
        self.client = APIClient()

        self.owner = User.objects.create_user(phone_number="998901000001", password="pass")
        self.other = User.objects.create_user(phone_number="998901000002", password="pass")
        self.superadmin = User.objects.create_user(
            phone_number="998901000003", password="pass", role=User.UserRoles.SUPERADMIN
        )

        self.device = Devices.objects.create(
            user=self.owner,
            name="D1",
            ip="10.0.0.1",
            username="admin",
            password="admin",
            status=Devices.Status.ACTIVE,
        )
        self.branch = Branch.objects.create(user=self.owner, name="Branch1", device=self.device)
        self.employee = Employee.objects.create(
            device=self.device,
            employee_no="EMP001",
            name="Test Employee",
        )

    def test_owner_can_view_own_employee(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f"/person/employee-detail/{self.employee.id}/")
        self.assertEqual(response.status_code, 200)

    def test_other_authenticated_user_cannot_view_employee(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.get(f"/person/employee-detail/{self.employee.id}/")
        self.assertEqual(response.status_code, 403)

    def test_other_authenticated_user_cannot_update_employee(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.put(f"/person/update/{self.employee.id}/", {"name": "Hacked"}, format="json")
        self.assertEqual(response.status_code, 403)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.name, "Test Employee")

    def test_other_authenticated_user_cannot_delete_employee(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.delete(f"/person/delete/{self.employee.id}/")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Employee.objects.filter(id=self.employee.id).exists())

    def test_superadmin_can_view_any_employee(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get(f"/person/employee-detail/{self.employee.id}/")
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_cannot_view_employee(self):
        response = self.client.get(f"/person/employee-detail/{self.employee.id}/")
        self.assertEqual(response.status_code, 401)

    def test_employee_not_found_returns_404(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get("/person/employee-detail/99999/")
        self.assertEqual(response.status_code, 404)


@override_settings(SECURE_SSL_REDIRECT=False)
class EmployeeListTests(TestCase):
    client: APIClient

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(phone_number="998902000001", password="pass")
        self.device = Devices.objects.create(
            user=self.user,
            name="D2",
            ip="10.0.0.2",
            username="admin",
            password="admin",
            status=Devices.Status.ACTIVE,
        )
        self.branch = Branch.objects.create(user=self.user, name="Branch2", device=self.device)
        Employee.objects.create(device=self.device, employee_no="E1", name="Alice")
        Employee.objects.create(device=self.device, employee_no="E2", name="Bob")

    def test_list_requires_branch_id(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/person/employees/")
        self.assertEqual(response.status_code, 400)

    def test_list_returns_branch_employees(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/person/employees/?branch_id={self.branch.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_list_requires_auth(self):
        response = self.client.get(f"/person/employees/?branch_id={self.branch.id}")
        self.assertEqual(response.status_code, 401)


class PersonUtilsTests(TestCase):
    def test_normalize_employee_no(self):
        self.assertEqual(normalize_employee_no(None), "")
        self.assertEqual(normalize_employee_no(" 12 "), "12")
        self.assertEqual(normalize_employee_no(12), "12")

    def test_format_late(self):
        self.assertIsNone(format_late(None))
        self.assertEqual(format_late(75), "1:15")
        self.assertEqual(format_late(5), "0:05")

    def test_fix_hikvision_time(self):
        begin, end = fix_hikvision_time(datetime(2026, 1, 5, 8, 30), datetime(2026, 1, 5, 10, 0))
        self.assertEqual(begin, "2026-01-05T08:30:00")
        self.assertEqual(end, "2026-01-05T23:59:59")


class HikvisionServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone_number="998908000001", password="pass")
        self.device = Devices.objects.create(
            user=self.user,
            name="HV",
            ip="10.0.0.9",
            username="admin",
            password="admin",
            status=Devices.Status.ACTIVE,
        )

    @patch("person.services.hikvision.requests.post")
    def test_search_users_returns_user_list(self, mock_post):
        mock_post.return_value.json.return_value = {"UserInfoSearch": {"UserInfo": [{"employeeNo": "1"}]}}

        users = HikvisionService.search_users(self.device)

        self.assertEqual(users, [{"employeeNo": "1"}])
        url = mock_post.call_args.args[0]
        self.assertIn("10.0.0.9", url)
        self.assertIn("UserInfo/Search", url)

    @patch("person.services.hikvision.requests.post")
    def test_search_users_empty_response(self, mock_post):
        mock_post.return_value.json.return_value = {}

        self.assertEqual(HikvisionService.search_users(self.device), [])

    @patch("person.services.hikvision.requests.put")
    def test_delete_user_sends_employee_no(self, mock_put):
        HikvisionService.delete_user(self.device, "77")

        payload = mock_put.call_args.kwargs["json"]
        self.assertEqual(payload["UserInfoDelCond"]["EmployeeNoList"], [{"employeeNo": "77"}])


class FirstLastEventsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone_number="998908000002", password="pass")
        self.device = Devices.objects.create(
            user=self.user,
            name="D9",
            ip="10.0.0.10",
            username="admin",
            password="admin",
            status=Devices.Status.ACTIVE,
        )
        self.employee = Employee.objects.create(device=self.device, employee_no="E9", name="Evt Employee")

    def _event(self, serial, hour, label):
        return AccessEvent.objects.create(
            employee=self.employee,
            serial_no=serial,
            time=make_aware(datetime(2026, 6, 10, hour, 0)),
            major=5,
            minor=75,
            major_name="m",
            minor_name="n",
            name="Evt Employee",
            employee_no="E9",
            picture_url="",
            raw_json={},
            device=self.device,
            label_name=label,
        )

    def test_first_entry_and_last_exit(self):
        self._event("a1", 9, "KIRISH")
        self._event("a2", 12, "KIRISH")
        self._event("a3", 18, "CHIQISH")

        first, last = get_first_last_events(self.employee, date(2026, 6, 10))

        self.assertEqual(first.serial_no, "a1")
        self.assertEqual(last.serial_no, "a3")

    def test_no_events_returns_none_pair(self):
        first, last = get_first_last_events(self.employee, date(2026, 6, 11))

        self.assertIsNone(first)
        self.assertIsNone(last)
