from django.db import models


class AccessEvent(models.Model):
    serial_no = models.IntegerField(unique=True)
    time = models.DateTimeField()
    major = models.IntegerField()
    minor = models.IntegerField()
    major_name = models.CharField(max_length=100, null=True, blank=True)
    minor_name = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    employee_no = models.CharField(max_length=50, null=True, blank=True)
    picture_url = models.TextField(null=True, blank=True)
    raw_json = models.JSONField()

    def __str__(self):
        return f"{self.time} | {self.name} | minor={self.minor}"
