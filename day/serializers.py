from rest_framework import serializers
from day.models import DayOff, WorkDay, Shift, BreakTime


class DayOffGetSerializer(serializers.ModelSerializer):
    days = serializers.ListField(child=serializers.ChoiceField(choices=DayOff.WEEK_DAYS))

    class Meta:
        model = DayOff
        fields = "__all__"


class DayOffCreateSerializer(serializers.ModelSerializer):
    days = serializers.ListField(child=serializers.ChoiceField(choices=DayOff.WEEK_DAYS))

    class Meta:
        model = DayOff
        fields = ['name', 'days']


class WorkDayGetSerializer(serializers.ModelSerializer):
    days = serializers.ListField(child=serializers.ChoiceField(choices=WorkDay.WEEK_DAYS))

    class Meta:
        model = WorkDay
        fields = "__all__"


class WorkDayCreateSerializer(serializers.ModelSerializer):
    days = serializers.ListField(child=serializers.ChoiceField(choices=WorkDay.WEEK_DAYS))

    class Meta:
        model = WorkDay
        fields = ['name', 'days']


class BreakTimeGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = BreakTime
        fields = "__all__"


class BreakTimeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkDay
        fields = ['name', 'days']


class ShiftGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = "__all__"


class ShiftCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ['break_time', 'name', 'start_time', 'end_time']
