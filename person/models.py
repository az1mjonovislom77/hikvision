from django.db import models
from day.models import Shift, BreakTime, WorkDay, DayOff
from user.models import User
from utils.models import Department, Branch


class Employee(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    employee_no = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    user_type = models.CharField(max_length=50, default="normal")
    employment = models.CharField(max_length=250, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    position = models.CharField(max_length=250, null=True, blank=True)
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=250, null=True, blank=True)
    phone_number = models.CharField(max_length=50, null=True, blank=True)
    salary = models.FloatField(default=0)
    break_time = models.ForeignKey(BreakTime, on_delete=models.SET_NULL, null=True, blank=True)
    work_day = models.ForeignKey(WorkDay, on_delete=models.SET_NULL, null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    fine = models.FloatField(default=0)
    day_off = models.ForeignKey(DayOff, on_delete=models.SET_NULL, null=True, blank=True)
    begin_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    door_right = models.CharField(max_length=50, default="1")
    face_url = models.CharField(max_length=500, null=True, blank=True)
    face_image = models.ImageField(upload_to="faces/", null=True, blank=True)
    raw_json = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee_no} - {self.name}"
