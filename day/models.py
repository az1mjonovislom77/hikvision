from django.db import models
from utils.base.model_base import OwnedNamedModel


class DayOff(OwnedNamedModel):
    days = models.JSONField(default=list)


class WorkDay(OwnedNamedModel):
    days = models.JSONField(default=list)


class BreakTime(OwnedNamedModel):
    start_time = models.TimeField()
    end_time = models.TimeField()


class Shift(OwnedNamedModel):
    break_time = models.ForeignKey(BreakTime, on_delete=models.SET_NULL, null=True, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
