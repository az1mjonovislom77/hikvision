from rest_framework import serializers
from user.models import User
from user.services.user_service import UserService
from utils.models import Subscription
from django.utils import timezone


class ActiveSubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name")
    plan_type = serializers.CharField(source="plan.plan_type")
    billing_cycle = serializers.CharField(source="plan.billing_cycle")

    class Meta:
        model = Subscription
        fields = ["plan_name", "plan_type", "billing_cycle", "start_date", "end_date", ]


class UserDetailSerializer(serializers.ModelSerializer):
    active_subscription = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "full_name", "phone_number", "role", "is_active", "active_subscription", ]

    def get_active_subscription(self, user):
        subscription = Subscription.objects.filter(user=user, is_active=True,
                                                   end_date__gt=timezone.now()).select_related("plan").first()

        if not subscription:
            return None

        return ActiveSubscriptionSerializer(subscription).data


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'phone_number', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return UserService.create_user(validated_data)

    def update(self, instance, validated_data):
        return UserService.update_user(instance, validated_data)
