from rest_framework import serializers
from day.models import DayOff, WorkDay, Shift, BreakTime


class DayOffSerializer(serializers.ModelSerializer):
    class Meta:
        model = DayOff
        fields = "__all__"


class WorkDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkDay
        fields = "__all__"


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = "__all__"


class BreakTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BreakTime
        fields = "__all__"
