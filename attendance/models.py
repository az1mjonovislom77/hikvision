from django.db import models, transaction
from attendance.utils import count_workdays_in_month
from person.models import Employee


class AttendanceDaily(models.Model):
    STATUS_CHOICES = (
        ("sbk", "Sababli kelmadi"),
        ("szk", "Sababsiz kelmadi"),
    )

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)
    comment = models.CharField(max_length=255, null=True, blank=True)
    fine_amount = models.FloatField(default=0)

    class Meta:
        unique_together = ("employee", "date")

    def save(self, *args, **kwargs):
        emp = self.employee

        old = None
        if self.pk:
            old = AttendanceDaily.objects.filter(pk=self.pk) \
                .only("status", "fine_amount").first()

        with transaction.atomic():

            if old and old.status == "szk" and self.status == "sbk":
                if old.fine_amount:
                    emp.fine -= old.fine_amount
                    emp.save(update_fields=["fine"])
                self.fine_amount = 0

            elif self.status == "szk":
                year = self.date.year
                month = self.date.month

                workdays = count_workdays_in_month(emp.work_day, emp.day_off, year, month)

                if workdays > 0:
                    day_salary = emp.salary / workdays
                    self.fine_amount = round(day_salary, 2)

                    emp.fine += self.fine_amount
                    emp.save(update_fields=["fine"])

            else:
                self.fine_amount = 0

            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.name} — {self.date} — {self.status}"
