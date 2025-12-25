from rest_framework import serializers

from utils.base.serializers_base import BaseReadSerializer
from utils.models import Devices, Department, Branch, TelegramChannel, Plan, Subscription, Notification


class DevicesSerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = Devices


class DepartmentGetSerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = Department


class DepartmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["name"]


class BranchGetSerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = Branch


class BranchCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["name"]


class TelegramChannelSerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = TelegramChannel


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ["id", "title", "plan_type", "billing_cycle", "duration_months", "price", "description", "currency",
                  "content"]
        read_only_fields = ["id", "duration_months"]


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    plan_id = serializers.PrimaryKeyRelatedField(queryset=Plan.objects.all(), source="plan", write_only=True)

    class Meta:
        model = Subscription
        fields = ["plan_id"]


class SubscriptionDetailSerializer(serializers.ModelSerializer):
    plan = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ["id", "plan", "start_date", "end_date", "is_active", ]

    def get_plan(self, obj):
        return {"id": obj.plan.id,
                "title": obj.plan.title,
                "plan_type": obj.plan.plan_type,
                "billing_cycle": obj.plan.billing_cycle,
                "price": obj.plan.price
                }


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "user", "text", "created_at"]


class AdminNotificationSerializer(serializers.Serializer):
    user_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    text = serializers.CharField()
