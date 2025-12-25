from rest_framework import serializers


class ReadWriteSerializerMixin:
    write_actions = {"create", "update", "partial_update"}
    write_serializer = None
    read_serializer = None

    def get_serializer_class(self):
        if self.action in self.write_actions:
            return self.write_serializer or self.serializer_class
        return self.read_serializer or self.serializer_class


class BaseReadSerializer(serializers.ModelSerializer):
    class Meta:
        abstract = True
        fields = "__all__"
