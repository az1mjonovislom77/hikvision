from django.db import models
from user.models import User


class DayOff(models.Model):
    WEEK_DAYS = [
        ('mon', 'Dushanba'),
        ('tue', 'Seshanba'),
        ('wed', 'Chorshanba'),
        ('thu', 'Payshanba'),
        ('fri', 'Juma'),
        ('sat', 'Shanba'),
        ('sun', 'Yakshanba'),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=250)
    days = models.JSONField(default=list)

    def __str__(self):
        return self.name


class WorkDay(models.Model):
    WEEK_DAYS = [
        ('mon', 'Dushanba'),
        ('tue', 'Seshanba'),
        ('wed', 'Chorshanba'),
        ('thu', 'Payshanba'),
        ('fri', 'Juma'),
        ('sat', 'Shanba'),
        ('sun', 'Yakshanba'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=250)
    days = models.JSONField(default=list)

    def __str__(self):
        return self.name


class Shift(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=250, null=True, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return self.name


class BreakTime(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=250)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return self.name
