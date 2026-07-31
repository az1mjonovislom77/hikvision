import logging
from datetime import date

from celery import shared_task

from attendance.models import AttendanceDaily
from event.models import AccessEvent
from person.models import Employee

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={"max_retries": 3})
def mark_daily_attendance(self, target_date_str=None):
    target_date = date.fromisoformat(target_date_str) if target_date_str else date.today()

    logger.info("mark_daily_attendance started: date=%s", target_date)

    employees_with_events = set(
        AccessEvent.objects.filter(time__date=target_date).values_list("employee_id", flat=True).distinct()
    )

    count = 0
    for emp in Employee.objects.only("id"):
        status = "present" if emp.id in employees_with_events else "absent_unexcused"
        AttendanceDaily.objects.update_or_create(employee=emp, date=target_date, defaults={"status": status})
        count += 1

    logger.info("mark_daily_attendance done: date=%s processed=%d", target_date, count)
    return {"date": str(target_date), "processed": count}
