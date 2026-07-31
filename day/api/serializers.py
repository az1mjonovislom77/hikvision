from rest_framework import serializers

from day.models import BreakTime, DayOff, Shift, WorkDay
from utils.utils.constants import WEEK_DAYS


class WeekDaysField(serializers.ListField):
    def __init__(self, **kwargs):
        super().__init__(child=serializers.ChoiceField(choices=WEEK_DAYS), **kwargs)


class DayOffGetSerializer(serializers.ModelSerializer):
    days = WeekDaysField()

    class Meta:
        model = DayOff
        fields = "__all__"


class DayOffCreateSerializer(serializers.ModelSerializer):
    days = WeekDaysField()

    class Meta:
        model = DayOff
        fields = ["name", "days"]


class WorkDayGetSerializer(serializers.ModelSerializer):
    days = WeekDaysField()

    class Meta:
        model = WorkDay
        fields = "__all__"


class WorkDayCreateSerializer(serializers.ModelSerializer):
    days = WeekDaysField()

    class Meta:
        model = WorkDay
        fields = ["name", "days"]


class BreakTimeGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = BreakTime
        fields = "__all__"


class BreakTimeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BreakTime
        fields = ["name", "start_time", "end_time"]


class ShiftGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = "__all__"


class ShiftCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ["break_time", "name", "start_time", "end_time", "approved_late_min"]
