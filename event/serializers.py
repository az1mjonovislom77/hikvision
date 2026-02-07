from .models import AccessEvent
from rest_framework import serializers


class AccessEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessEvent
        fields = "__all__"
