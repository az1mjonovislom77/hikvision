from rest_framework import serializers
from person.models import Person


class PersonSerializer(serializers.ModelSerializer):
    data = serializers.SerializerMethodField()
    local_face = serializers.SerializerMethodField()

    class Meta:
        model = Person
        fields = ["data", "local_face", ]

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


class PersonCreateSerializer(serializers.Serializer):
    name = serializers.CharField()
    user_type = serializers.CharField(default="normal")
    begin_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    door_right = serializers.CharField(default="1")


class FaceCreateSerializer(serializers.Serializer):
    employee_no = serializers.CharField()
    image = serializers.ImageField()


class PersonUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    user_type = serializers.CharField(required=False)
    begin_time = serializers.DateTimeField(required=False)
    end_time = serializers.DateTimeField(required=False)
    door_right = serializers.CharField(required=False)
