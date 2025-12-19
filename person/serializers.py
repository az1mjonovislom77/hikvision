from rest_framework import serializers
from person.models import Employee, EmployeeHistory


class EmployeeSerializer(serializers.ModelSerializer):
    local_face = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = ["id", "device", "employee_no", "name", "user_type", "employment", "department", "position", "shift",
                  "description", "phone_number", "salary", "break_time", "work_day", "branch", "fine", "day_off",
                  "begin_time", "end_time", "door_right", "face_url", "local_face", "created_at"]

    def get_local_face(self, obj):
        if obj.face_image:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.face_image.url)
        return None


class EmployeeCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    user_type = serializers.CharField(default="normal")
    begin_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    door_right = serializers.CharField(default="1")

    class Meta:
        model = Employee
        fields = ["device", "name", "user_type", "begin_time", "end_time", "door_right", "employment", "department",
                  "position", "shift", "description", "phone_number", "salary", "break_time", "work_day", "branch",
                  "fine", "day_off"]


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ["device", "name", "user_type", "begin_time", "end_time", "door_right", "employment", "department",
                  "position", "shift", "description", "phone_number", "salary", "break_time", "work_day", "branch",
                  "fine", "day_off"]
        extra_kwargs = {"name": {"required": False}}


class EmployeeHistorySerializer(serializers.ModelSerializer):
    label_name = serializers.CharField(source="event.label_name", read_only=True)

    class Meta:
        model = EmployeeHistory
        fields = ["id", "event_time", "label_name", ]
