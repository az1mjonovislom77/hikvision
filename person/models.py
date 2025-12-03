from django.db import models
from day.models import Shift, BreakTime, WorkDay, DayOff
from utils.models import Department, Branch


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


class Staff(models.Model):
    person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=200)
    employment = models.CharField(max_length=250)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    position = models.CharField(max_length=250)
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=250)
    phone_number = models.CharField(max_length=50)
    salary = models.FloatField(default=0)
    break_time = models.ForeignKey(BreakTime, on_delete=models.SET_NULL, null=True, blank=True)
    work_day = models.ForeignKey(WorkDay, on_delete=models.SET_NULL, null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    fine = models.FloatField(default=0)
    day_off = models.ForeignKey(DayOff, on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField(upload_to="faces/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name
