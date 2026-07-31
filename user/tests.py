from django.http import HttpResponse
from django.test import TestCase, override_settings
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from user.models import User
from user.services.auth_service import AuthService
from user.services.token_service import UserTokenService
from user.services.user_service import UserService


@override_settings(SECURE_SSL_REDIRECT=False)
class AuthTests(TestCase):
    client: APIClient

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(phone_number="998901111111", password="testpass123")

    def test_signin_returns_access_token(self):
        response = self.client.post(
            "/user/login/",
            {
                "phone_number": "998901111111",
                "password": "testpass123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data["data"])

    def test_signin_wrong_password_returns_error(self):
        response = self.client.post(
            "/user/login/",
            {
                "phone_number": "998901111111",
                "password": "wrongpassword",
            },
            format="json",
        )
        self.assertIn(response.status_code, [400, 401])

    def test_signin_unknown_phone_returns_error(self):
        response = self.client.post(
            "/user/login/",
            {
                "phone_number": "998900000000",
                "password": "testpass123",
            },
            format="json",
        )
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


class UserManagerTests(TestCase):
    def test_create_superuser_sets_flags(self):
        admin = User.objects.create_superuser(phone_number="998902222222", password="pass")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_create_user_requires_phone_number(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(phone_number="", password="pass")


class UserServiceTests(TestCase):
    def test_create_user_hashes_password(self):
        user = UserService.create_user({"phone_number": "998903333333", "password": "secret123"})
        self.assertNotEqual(user.password, "secret123")
        self.assertTrue(user.check_password("secret123"))

    def test_update_user_keeps_password_when_not_given(self):
        user = User.objects.create_user(phone_number="998904444444", password="secret123")
        UserService.update_user(user, {"full_name": "New Name"})
        user.refresh_from_db()
        self.assertEqual(user.full_name, "New Name")
        self.assertTrue(user.check_password("secret123"))

    def test_update_user_changes_password_when_given(self):
        user = User.objects.create_user(phone_number="998905555555", password="secret123")
        UserService.update_user(user, {"password": "newpass456"})
        user.refresh_from_db()
        self.assertTrue(user.check_password("newpass456"))


class TokenServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone_number="998906666666", password="pass")

    def test_get_tokens_for_user_returns_pair(self):
        tokens = UserTokenService.get_tokens_for_user(self.user)
        self.assertIn("access", tokens)
        self.assertIn("refresh", tokens)

    def test_refresh_cookie_set_and_clear(self):
        response = HttpResponse()
        UserTokenService.set_refresh_cookie(response, "token-value")
        cookie = response.cookies[UserTokenService.COOKIE_NAME]
        self.assertEqual(cookie.value, "token-value")
        self.assertTrue(cookie["httponly"])
        UserTokenService.clear_refresh_cookie(response)
        self.assertEqual(response.cookies[UserTokenService.COOKIE_NAME].value, "")

    def test_valid_refresh_token_returns_access(self):
        refresh = str(RefreshToken.for_user(self.user))
        access = UserTokenService.get_tokens_for_user_from_refresh(refresh)
        self.assertTrue(access)

    def test_invalid_refresh_token_raises(self):
        with self.assertRaises(TokenError):
            UserTokenService.get_tokens_for_user_from_refresh("bogus-token")


class AuthServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone_number="998907777777", password="secret123")

    def test_authenticate_valid_credentials(self):
        user = AuthService.authenticate_user("998907777777", "secret123")
        self.assertEqual(user.id, self.user.id)

    def test_authenticate_wrong_password_raises(self):
        with self.assertRaises(ValidationError):
            AuthService.authenticate_user("998907777777", "wrong")

    def test_logout_with_invalid_token_raises(self):
        with self.assertRaises(ValidationError):
            AuthService.logout_user("bogus-token")

    def test_logout_blacklists_valid_token(self):
        refresh = str(RefreshToken.for_user(self.user))
        AuthService.logout_user(refresh)
        with self.assertRaises(ValidationError):
            AuthService.logout_user(refresh)
