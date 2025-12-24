from rest_framework import serializers
from utils.constants import WEEK_DAYS


class WeekDaysField(serializers.ListField):
    def __init__(self, **kwargs):
        super().__init__(child=serializers.ChoiceField(choices=WEEK_DAYS), **kwargs)
