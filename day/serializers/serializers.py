from rest_framework import serializers
from day.serializers.fields import WeekDaysField
from day.models import DayOff, WorkDay, Shift, BreakTime
from utils.base.serializers_base import BaseReadSerializer


class DayOffGetSerializer(serializers.ModelSerializer):
    days = WeekDaysField()

    class Meta:
        model = DayOff
        fields = "__all__"


class DayOffCreateSerializer(serializers.ModelSerializer):
    days = WeekDaysField()

    class Meta:
        model = DayOff
        fields = ['name', 'days']


class WorkDayGetSerializer(serializers.ModelSerializer):
    days = WeekDaysField()

    class Meta:
        model = WorkDay
        fields = "__all__"


class WorkDayCreateSerializer(serializers.ModelSerializer):
    days = WeekDaysField()

    class Meta:
        model = WorkDay
        fields = ['name', 'days']


class BreakTimeGetSerializer(BaseReadSerializer):
    class Meta:
        model = BreakTime


class BreakTimeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BreakTime
        fields = ['name', 'start_time', 'end_time']


class ShiftGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = "__all__"


class ShiftCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ['break_time', 'name', 'start_time', 'end_time', 'approved_late_min']
