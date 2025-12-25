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


class Plan(models.Model):
    class PlanType(models.TextChoices):
        STANDARD = "standard", "Standard"
        PREMIUM = "premium", "Premium"

    class CycleChoice(models.TextChoices):
        MONTHLY = "monthly", "1 Month"
        QUARTERLY = "quarterly", "3 Months"
        HALF_YEARLY = "half_yearly", "6 Months"
        YEARLY = "yearly", "12 Months"

    name = models.CharField(max_length=50)
    plan_type = models.CharField(max_length=20, choices=PlanType.choices)
    billing_cycle = models.CharField(max_length=20, choices=CycleChoice.choices, null=False, blank=False, )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_months = models.PositiveIntegerField(editable=False)

    def save(self, *args, **kwargs):
        self.duration_months = {
            self.CycleChoice.MONTHLY: 1,
            self.CycleChoice.QUARTERLY: 3,
            self.CycleChoice.HALF_YEARLY: 6,
            self.CycleChoice.YEARLY: 12,
        }[self.billing_cycle]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.duration_months} months)"


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.plan}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.text}"


class TelegramChannel(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    chat_id = models.CharField(max_length=200)
    resolved_id = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name
