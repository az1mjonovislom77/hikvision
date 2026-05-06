from django.db.models import Prefetch
from event.models import AccessEvent
from person.models import Employee, EmployeeHistory
from user.models import User
from utils.models import Branch, Devices


def get_target_user(*, user_id):
    return User.objects.filter(id=user_id).first()


def get_user_branch(*, branch_id, user):
    return Branch.objects.filter(id=branch_id, user=user).first()


def get_device(*, device_id, user=None):
    qs = Devices.objects.filter(id=device_id)
    if user is not None:
        qs = qs.filter(user=user)
    return qs.first()


def get_branch_device_queryset(*, branch):
    return Devices.objects.filter(id=branch.device_id)


def get_branch_employees(*, branch):
    return Employee.objects.filter(device=branch.device).select_related("device")


def get_user_employees_with_events(*, user):
    return (
        Employee.objects
        .filter(device__user=user)
        .select_related("shift", "device")
        .prefetch_related(Prefetch("device__accessevent_set",
                                   queryset=AccessEvent.objects.order_by("time"),
                                   to_attr="prefetched_events"))
    )


def get_employee_with_device_user(*, employee_id):
    return Employee.objects.select_related("device__user").filter(id=employee_id).first()


def get_employee_history_for_day(*, employee_id, start, end):
    return (
        EmployeeHistory.objects
        .filter(employee_id=employee_id, event_time__range=(start, end))
        .select_related("event", "employee")
    )


def empty_employee_history_queryset():
    return EmployeeHistory.objects.none()


def get_access_events_for_history(*, employee_no, device, start, end):
    return (
        AccessEvent.objects
        .filter(employee_no=employee_no, device=device, time__range=(start, end))
        .only("id", "time", "label_name")
    )


def get_existing_employee_history_event_ids(*, employee, events):
    return set(
        EmployeeHistory.objects.filter(
            employee=employee,
            event_id__in=[e.id for e in events],
        ).values_list("event_id", flat=True)
    )

