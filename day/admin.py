from django.contrib import admin
from day.models import DayOff, WorkDay, Shift, BreakTime
from utils.base.admin_base import NameOnlyAdmin


@admin.register(DayOff)
class DayOffAdmin(NameOnlyAdmin):
    pass


@admin.register(WorkDay)
class WorkDayAdmin(NameOnlyAdmin):
    pass


@admin.register(Shift)
class ShiftAdmin(NameOnlyAdmin):
    pass


@admin.register(BreakTime)
class BreakTimeAdmin(NameOnlyAdmin):
    pass
