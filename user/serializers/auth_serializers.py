from rest_framework import serializers
from user.models import User
from user.services.auth_service import AuthService
from utils.models import Subscription
from django.utils import timezone


class SignInSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = AuthService.authenticate_user(phone_number=attrs.get('phone_number'), password=attrs.get('password'))
        attrs['user'] = user
        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def save(self, **kwargs):
        AuthService.logout_user(self.validated_data['refresh'])


class MeSerializer(serializers.ModelSerializer):
    subscription = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "full_name", "phone_number", "role", "is_active", "subscription")

    def get_subscription(self, user):
        subscription = Subscription.objects.filter(user=user, is_active=True,
                                                   end_date__gt=timezone.now()).select_related("plan").first()

        if not subscription:
            return None

        return {
            "plan_name": subscription.plan.name,
            "plan_type": subscription.plan.plan_type,
            "billing_cycle": subscription.plan.billing_cycle,
            "is_paid": subscription.is_paid,
            "is_active": subscription.is_active,
            "start_date": subscription.start_date,
            "end_date": subscription.end_date,
        }
