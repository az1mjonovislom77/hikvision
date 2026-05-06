from user.models import User
from utils.models import Branch, Department, Devices, Notification, Plan, Subscription, TelegramChannel


def devices_queryset():
    return Devices.objects.all()


def department_queryset():
    return Department.objects.all()


def branch_queryset():
    return Branch.objects.all()


def telegram_channel_queryset():
    return TelegramChannel.objects.all()


def plan_queryset():
    return Plan.objects.all()


def subscription_queryset():
    return Subscription.objects.select_related("plan")


def notification_queryset():
    return Notification.objects.all()


def notification_queryset_for_user(*, user):
    qs = notification_queryset()

    if user.is_staff or user.role == User.UserRoles.SUPERADMIN:
        return qs.select_related("user").order_by("-created_at")

    return qs.filter(user=user).order_by("-created_at")

