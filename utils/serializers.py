from rest_framework import serializers
from utils.models import Devices, Department, Branch, TelegramChannel, Plan, Subscription


class DevicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Devices
        fields = '__all__'


class DepartmentGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class DepartmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['name', ]


class BranchGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'


class BranchCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['name', ]


class TelegramChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramChannel
        fields = '__all__'


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ["id", "name", "plan_type", "billing_cycle", "duration_months", "price", ]
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
        return {"id": obj.plan.id, "name": obj.plan.name, "plan_type": obj.plan.plan_type,
                "billing_cycle": obj.plan.billing_cycle, "price": obj.plan.price, }
