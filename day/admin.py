from django.contrib import admin
from utils.base.admin_base import NameOnlyAdmin
from day.models import DayOff, WorkDay, Shift, BreakTime


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
