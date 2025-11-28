from rest_framework import serializers
from user.models import User
from user.services.auth_service import AuthService


class SignInSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = AuthService.authenticate_user(
            phone_number=attrs.get('phone_number'),
            password=attrs.get('password')
        )
        attrs['user'] = user
        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def save(self, **kwargs):
        AuthService.logout_user(self.validated_data['refresh'])


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "full_name", "phone_number", "role", "is_active")
