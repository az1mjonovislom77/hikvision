from attendance.selectors.selectors import get_user_branch
from attendance.services.attendance import AttendanceService
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


def get_monthly_report_for_excel(*, user, branch_id, year, month, employee_id=None):
    branch = get_user_branch(branch_id=branch_id, user=user)

    if not branch:
        return None

    return AttendanceService.monthly_report_payload(branch=branch, employee_id=employee_id, year=year, month=month)
