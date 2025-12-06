from rest_framework import serializers
from user.models import User
from user.services.user_service import UserService


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'phone_number', 'role', 'is_active']


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'phone_number', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return UserService.create_user(validated_data)

    def update(self, instance, validated_data):
        return UserService.update_user(instance, validated_data)
