from django.db import models
from user.models import User
from utils.base.model_base import TimeStampedModel, OwnedNamedModel


class Devices(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "active"
        INACTIVE = "inactive", "inactive"

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    ip = models.CharField(max_length=150, null=True, blank=True)
    username = models.CharField(max_length=150, null=True, blank=True)
    password = models.CharField(max_length=150, null=True, blank=True)
    status = models.CharField(max_length=100, choices=Status.choices)

    def __str__(self):
        return self.name


class Department(OwnedNamedModel):
    pass


class Branch(OwnedNamedModel):
    pass


class Plan(models.Model):
    class PlanType(models.TextChoices):
        FREE = "free", "Free"
        GO = "go", "Go"
        PLUS = "plus", "Plus"

    class CycleChoice(models.TextChoices):
        MONTHLY = "monthly", "1 Month"
        QUARTERLY = "quarterly", "3 Months"
        HALF_YEARLY = "half_yearly", "6 Months"
        YEARLY = "yearly", "12 Months"

    title = models.CharField(max_length=50)
    plan_type = models.CharField(max_length=20, choices=PlanType.choices)
    billing_cycle = models.CharField(max_length=20, choices=CycleChoice.choices, null=False, blank=False)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=200, null=True, blank=True)
    duration_months = models.PositiveIntegerField(editable=False)
    description = models.TextField(null=True, blank=True, max_length=500)
    content = models.TextField(null=True, blank=True, max_length=500)

    def save(self, *args, **kwargs):
        self.duration_months = {
            self.CycleChoice.MONTHLY: 1,
            self.CycleChoice.QUARTERLY: 3,
            self.CycleChoice.HALF_YEARLY: 6,
            self.CycleChoice.YEARLY: 12,
        }[self.billing_cycle]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.duration_months} months)"


class Subscription(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - {self.plan}"


class Notification(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    text = models.TextField()

    def __str__(self):
        return f"{self.user} - {self.text}"


class TelegramChannel(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    chat_id = models.CharField(max_length=200)
    resolved_id = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.name
