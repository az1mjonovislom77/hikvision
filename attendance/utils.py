import calendar
from datetime import date

from utils.utils.constants import WEEKDAY_CODE_MAP


def count_workdays_in_month(workday_obj, dayoff_obj, year, month):
    if not workday_obj or not workday_obj.days:
        return 0

    workdays = set(workday_obj.days)
    dayoffs = set(dayoff_obj.days) if dayoff_obj else set()

    total = 0
    days_in_month = calendar.monthrange(year, month)[1]

    for d in range(1, days_in_month + 1):
        day = date(year, month, d)
        weekday_code = WEEKDAY_CODE_MAP[day.weekday()]

        if weekday_code in dayoffs:
            continue

        if weekday_code in workdays:
            total += 1

    return total
