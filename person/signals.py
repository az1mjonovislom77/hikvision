from django.db.models.signals import post_save
from django.dispatch import receiver

from event.models import AccessEvent
from person.models import EmployeeHistory, Employee


@receiver(post_save, sender=AccessEvent)
def create_employee_history(sender, instance, created, **kwargs):
    if not created:
        return

    employee = instance.employee
    if not employee:
        try:
            employee = Employee.objects.get(
                employee_no=instance.employee_no,
                device=instance.device
            )
        except Employee.DoesNotExist:
            return

        instance.employee = employee
        instance.save(update_fields=["employee"])

    EmployeeHistory.objects.get_or_create(
        employee=employee,
        event=instance,
        defaults={
            "event_time": instance.time,
            "label_name": instance.label_name or instance.raw_json.get("label")
        }
    )
