from attendance.models import AttendanceDaily
from event.models import AccessEvent
from person.models import Employee
from utils.models import Branch


def get_user_branch(*, branch_id, user):
    return Branch.objects.filter(id=branch_id, user=user).first()


def get_branch_employees(*, branch):
    return Employee.objects.filter(device=branch.device).distinct()


def get_branch_employee(*, employee_id, branch):
    return Employee.objects.filter(id=employee_id, device=branch.device)


def get_employee(*, employee_id):
    return Employee.objects.get(id=employee_id)


def has_employee_entry_event(*, employee, target_date):
    return AccessEvent.objects.filter(employee=employee, time__date=target_date, major=5, minor=75).exists()


def get_absent_attendance_records(*, target_date):
    return AttendanceDaily.objects.filter(date=target_date, status__in=["sbk", "szk"])


def get_employee_attendance(*, employee, target_date):
    return AttendanceDaily.objects.filter(employee=employee, date=target_date).first()


def get_employee_day_events(*, employee, target_date):
    return AccessEvent.objects.filter(employee=employee, time__date=target_date).order_by("time")
