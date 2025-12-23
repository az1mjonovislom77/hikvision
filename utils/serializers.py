from rest_framework import serializers
from utils.models import Devices, Department, Branch, TelegramChannel


class DevicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Devices
        fields = '__all__'


class DepartmentGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class DepartmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['name', ]


class BranchGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['user', 'name', 'created_at']


class BranchCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['name', ]


class TelegramChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramChannel
        fields = '__all__'
