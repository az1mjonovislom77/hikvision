from django.db import models
from user.models import User


class Devices(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active",
        INACTIVE = "inactive",

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    ip = models.CharField(max_length=150, null=True, blank=True)
    username = models.CharField(max_length=150, null=True, blank=True)
    password = models.CharField(max_length=150, null=True, blank=True)
    status = models.CharField(choices=Status.choices, max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Department(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Branch(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Notifications(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text


class TelegramChannel(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    chat_id = models.CharField(max_length=200)
    resolved_id = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name
