from day.models import BreakTime, DayOff, Shift, WorkDay


def day_off_queryset():
    return DayOff.objects.all()


def work_day_queryset():
    return WorkDay.objects.all()


def shift_queryset():
    return Shift.objects.all()


def break_time_queryset():
    return BreakTime.objects.all()

