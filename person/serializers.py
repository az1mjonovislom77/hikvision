from rest_framework import serializers
from person.models import Employee


class EmployeeSerializer(serializers.ModelSerializer):
    data = serializers.SerializerMethodField()
    local_face = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = ["data", "local_face"]

    def get_local_face(self, obj):
        if obj.face_image:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.face_image.url)
        return None

    def get_data(self, obj):
        if not obj.raw_json:
            return {}

        cleaned = obj.raw_json.copy()
        cleaned.pop("faceURL", None)
        return cleaned


class EmployeeCreateSerializer(serializers.Serializer):
    name = serializers.CharField()
    user_type = serializers.CharField(default="normal")
    begin_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    door_right = serializers.CharField(default="1")


class EmployeeFaceSerializer(serializers.Serializer):
    employee_no = serializers.CharField()
    image = serializers.ImageField()


class EmployeeUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    user_type = serializers.CharField(required=False)
    begin_time = serializers.DateTimeField(required=False)
    end_time = serializers.DateTimeField(required=False)
    door_right = serializers.CharField(required=False)


class EmployeeStaffSerializer(serializers.ModelSerializer):
    local_face = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = ["id", "employee_no", "name", "employment", "department", "position", "shift", "description",
                  "phone_number", "salary", "break_time", "work_day", "branch", "fine", "day_off", "local_face"]

    def get_local_face(self, obj):
        if obj.face_image:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.face_image.url)
        return None
