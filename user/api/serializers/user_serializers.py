from rest_framework import serializers

from user.models import User
from user.selectors.user import get_active_subscription
from user.services.user_service import UserService
from utils.base.permissions import is_admin
from utils.models import Subscription


class ActiveSubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name")
    plan_type = serializers.CharField(source="plan.plan_type")
    billing_cycle = serializers.CharField(source="plan.billing_cycle")

    class Meta:
        model = Subscription
        fields = [
            "plan_name",
            "plan_type",
            "billing_cycle",
            "start_date",
            "end_date",
        ]


class UserDetailSerializer(serializers.ModelSerializer):
    active_subscription = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "phone_number",
            "role",
            "is_active",
            "active_subscription",
        ]

    def get_active_subscription(self, user):
        subscription = get_active_subscription(user=user)

        if not subscription:
            return None

        return ActiveSubscriptionSerializer(subscription).data


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "full_name", "phone_number", "password", "role"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_role(self, value):
        request = self.context.get("request")

        if request and not is_admin(request.user):
            raise serializers.ValidationError("Bu maydonni faqat admin o'zgartira oladi")

        return value

    def create(self, validated_data):
        return UserService.create_user(validated_data)

    def update(self, instance, validated_data):
        return UserService.update_user(instance, validated_data)
