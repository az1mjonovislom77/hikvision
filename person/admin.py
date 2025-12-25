from django.contrib import admin
from person.models import Employee
from utils.base.admin_base import NameOnlyAdmin


@admin.register(Employee)
class EmployeeAdmin(NameOnlyAdmin):
    pass
