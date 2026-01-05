from django.contrib import admin
from .models import AttendanceDaily


@admin.register(AttendanceDaily)
class AttendanceDailyAdmin(admin.ModelAdmin):
    list_display = ("employee", "date", "status", "comment")
    list_filter = ("status", "date", "employee")
    search_fields = ("employee__name",)
