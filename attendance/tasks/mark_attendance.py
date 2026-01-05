from datetime import date
from django.db.models import Min
from event.models import AccessEvent
from attendance.models import AttendanceDaily
from person.models import Employee


def mark_daily_attendance(target_date=None):
    target_date = target_date or date.today()

    for emp in Employee.objects.all():

        first_event = (
            AccessEvent.objects.filter(employee=emp, time__date=target_date)
            .aggregate(first_in=Min("time")))["first_in"]

        if first_event:
            status = "present"
        else:
            status = "absent_unexcused"

        AttendanceDaily.objects.update_or_create(employee=emp, date=target_date, defaults={"status": status})
