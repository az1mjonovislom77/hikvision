from django.contrib.auth import authenticate
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken, TokenError


class AuthService:

    @staticmethod
    def authenticate_user(phone_number, password):
        user = authenticate(phone_number=phone_number, password=password)
        if not user:
            raise ValidationError("Invalid phone number or password.")
        return user

    @staticmethod
    def logout_user(refresh_token):
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            raise ValidationError("Invalid or expired token.")
