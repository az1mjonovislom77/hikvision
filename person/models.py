from django.db import models


class Person(models.Model):
    employee_no = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    user_type = models.CharField(max_length=50, default="normal")
    begin_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    door_right = models.CharField(max_length=50, default="1")
    face_url = models.CharField(max_length=500, null=True, blank=True)
    face_image = models.ImageField(upload_to="faces/", null=True, blank=True)
    raw_json = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee_no} - {self.name}"
