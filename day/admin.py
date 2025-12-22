from django.contrib import admin
from day.models import DayOff, WorkDay, Shift, BreakTime


@admin.register(DayOff)
class DayOffAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(WorkDay)
class WorkDayAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(BreakTime)
class BreakTimeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
