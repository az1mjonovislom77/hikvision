from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from person.models import Employee
from user.models import User
from utils.models import Devices, Branch


@override_settings(SECURE_SSL_REDIRECT=False)
class EmployeePermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.owner = User.objects.create_user(phone_number="998901000001", password="pass")
        self.other = User.objects.create_user(phone_number="998901000002", password="pass")
        self.superadmin = User.objects.create_user(
            phone_number="998901000003", password="pass", role=User.UserRoles.SUPERADMIN
        )

        self.device = Devices.objects.create(
            user=self.owner, name="D1", ip="10.0.0.1",
            username="admin", password="admin", status=Devices.Status.ACTIVE,
        )
        self.branch = Branch.objects.create(user=self.owner, name="Branch1", device=self.device)
        self.employee = Employee.objects.create(
            device=self.device, employee_no="EMP001", name="Test Employee",
        )

    def test_owner_can_view_own_employee(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f"/person/employee-detail/{self.employee.id}/")
        self.assertEqual(response.status_code, 200)

    def test_other_authenticated_user_can_view_employee(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.get(f"/person/employee-detail/{self.employee.id}/")
        self.assertEqual(response.status_code, 200)

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
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(phone_number="998902000001", password="pass")
        self.device = Devices.objects.create(
            user=self.user, name="D2", ip="10.0.0.2",
            username="admin", password="admin", status=Devices.Status.ACTIVE,
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
