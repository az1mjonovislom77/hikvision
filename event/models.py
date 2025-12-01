from django.db import models


class AccessEvent(models.Model):
    serial_no = models.CharField(max_length=100, db_index=True)
    time = models.DateTimeField()
    major = models.IntegerField()
    minor = models.IntegerField()
    major_name = models.CharField(max_length=100)
    minor_name = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    employee_no = models.CharField(max_length=50)
    picture_url = models.TextField()
    raw_json = models.JSONField()

    class Meta:
        ordering = ['-time']
        indexes = [
            models.Index(fields=['-time']),
            models.Index(fields=['serial_no']),
            models.Index(fields=['major', 'minor']),
        ]

    def __str__(self):
        return f"{self.name} - {self.time}"
