from django.db import models


class Devices(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active",
        INACTIVE = "inactive",

    name = models.CharField(max_length=100)
    status = models.CharField(choices=Status.choices, max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Branch(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
