from django.db import models


class DayOff(models.Model):
    name = models.CharField(max_length=250)
    days = models.TextField(max_length=250)

    def __str__(self):
        return self.name


class WorkDay(models.Model):
    name = models.CharField(max_length=250)
    days = models.TextField(max_length=250)

    def __str__(self):
        return self.name


class Shift(models.Model):
    name = models.CharField(max_length=250, null=True, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return self.name


class BreakTime(models.Model):
    name = models.CharField(max_length=250)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return self.name
