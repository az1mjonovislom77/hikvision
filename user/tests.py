from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from user.models import User


@override_settings(SECURE_SSL_REDIRECT=False)
class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(phone_number="998901111111", password="testpass123")

    def test_signin_returns_access_token(self):
        response = self.client.post("/user/login/", {
            "phone_number": "998901111111",
            "password": "testpass123",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data["data"])

    def test_signin_wrong_password_returns_error(self):
        response = self.client.post("/user/login/", {
            "phone_number": "998901111111",
            "password": "wrongpassword",
        }, format="json")
        self.assertIn(response.status_code, [400, 401])

    def test_signin_unknown_phone_returns_error(self):
        response = self.client.post("/user/login/", {
            "phone_number": "998900000000",
            "password": "testpass123",
        }, format="json")
        self.assertIn(response.status_code, [400, 401])

    def test_me_endpoint_requires_auth(self):
        response = self.client.get("/user/me/")
        self.assertEqual(response.status_code, 401)

    def test_me_endpoint_returns_user_data(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/user/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["phone_number"], "998901111111")

    def test_refresh_without_cookie_returns_400(self):
        response = self.client.post("/user/auth/refresh/")
        self.assertEqual(response.status_code, 400)
