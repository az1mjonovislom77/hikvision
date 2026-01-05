from rest_framework import serializers

from attendance.models import AttendanceDaily


class AttendanceDailyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceDaily
        fields = ['employee', 'status', 'comment']
