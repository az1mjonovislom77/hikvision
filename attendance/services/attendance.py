from calendar import monthrange
from datetime import date, datetime, timedelta
from django.utils.timezone import localtime, make_aware, now
from attendance.models import AttendanceDaily
from attendance.selectors.selectors import get_absent_attendance_records, get_branch_employee, get_branch_employees, \
    get_employee, get_employee_attendance, get_employee_day_events, has_employee_entry_event
from attendance.utils import count_workdays_in_month, is_employee_workday, minutes_to_hm


class AttendanceService:
    @staticmethod
    def create_missing_absent_records(*, branch, target_date):
        today = date.today()
        current_dt = now()
        employees = get_branch_employees(branch=branch)

        for emp in employees:
            if not emp.shift or not emp.shift.start_time or not emp.shift.end_time:
                continue

            if not emp.work_day or not emp.work_day.days:
                continue

            if not is_employee_workday(emp.work_day, emp.day_off, target_date):
                continue

            shift_end = make_aware(datetime.combine(target_date, emp.shift.end_time))

            if target_date == today and current_dt < shift_end:
                continue

            has_event = has_employee_entry_event(employee=emp, target_date=target_date)

            if has_event:
                continue

            AttendanceDaily.objects.get_or_create(
                employee=emp,
                date=target_date,
                defaults={
                    "status": "szk",
                    "comment": "Kirish yoki chiqish eventi yoq"
                }
            )

    @staticmethod
    def absent_records_payload(*, target_date):
        records = get_absent_attendance_records(target_date=target_date)
        return {
            "date": target_date,
            "total": records.count(),
            "employees": [
                {
                    "employee_id": r.employee.id,
                    "employee_name": r.employee.name,
                    "status": r.status,
                    "status_label": r.get_status_display(),
                    "comment": r.comment,
                    "fine": r.fine_amount,
                    "date": r.date
                }for r in records
            ]
        }

    @staticmethod
    def update_daily_status(*, employee_id, target_date, status_value, comment):
        employee = get_employee(employee_id=employee_id)
        obj, created = AttendanceDaily.objects.update_or_create(
            employee=employee,
            date=target_date,
            defaults={"status": status_value, "comment": comment}
        )

        return {
            "created": created,
            "employee_id": employee.id,
            "employee_name": employee.name,
            "date": obj.date,
            "status": obj.status,
            "status_label": obj.get_status_display(),
            "fine_amount": obj.fine_amount
        }

    @staticmethod
    def monthly_report_payload(*, branch, employee_id, year, month):
        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])
        today = date.today()
        current_dt = now()

        employees = (
            get_branch_employee(employee_id=employee_id, branch=branch)
            if employee_id else
            get_branch_employees(branch=branch)
        )

        reports = []

        for emp in employees:
            workdays = count_workdays_in_month(emp.work_day, emp.day_off, year, month)
            day_salary = emp.salary / workdays if workdays else 0
            total_bonus = 0
            total_penalty = 0
            total_overtime = 0
            total_undertime = 0
            worked_minutes = 0
            sbk_count = 0
            szk_count = 0
            details = []
            shift_start_time = emp.shift.start_time.strftime("%H:%M") if emp.shift else None
            shift_end_time = emp.shift.end_time.strftime("%H:%M") if emp.shift else None

            for day in (start_date + timedelta(days=i)
                        for i in range((end_date - start_date).days + 1)):

                if day > today:
                    continue

                if not emp.shift or not emp.work_day:
                    continue

                if not is_employee_workday(emp.work_day, emp.day_off, day):
                    continue

                shift_start = datetime.combine(day, emp.shift.start_time)
                shift_end = datetime.combine(day, emp.shift.end_time)

                if day == today and current_dt < make_aware(shift_end):
                    continue

                attendance = get_employee_attendance(employee=emp, target_date=day)
                events = get_employee_day_events(employee=emp, target_date=day)
                shift_min = int((shift_end - shift_start).total_seconds() / 60)

                break_min = 0
                if emp.shift.break_time:
                    break_min = int(
                        (datetime.combine(day, emp.shift.break_time.end_time) -
                         datetime.combine(day, emp.shift.break_time.start_time)).total_seconds() / 60)

                shift_min -= break_min

                if not events.exists():
                    if attendance and attendance.status == "sbk":
                        sbk_count += 1
                        details.append({
                            "date": day,
                            "status": "sbk",
                            "status_label": "Sababli kelmadi",
                            "first_in": None,
                            "last_out": None,
                            "worked": "0:00",
                            "difference": "0:00",
                            "penalty": 0,
                            "bonus": 0,
                            "daily_total": 0,
                            "att_comment": attendance.comment if attendance else "",
                        })
                    else:
                        szk_count += 1
                        penalty_amount = round(day_salary, 2) if emp.is_fine else 0

                        if total_penalty + penalty_amount > emp.salary:
                            penalty_amount = max(0, emp.salary - total_penalty)

                        total_penalty += penalty_amount

                        details.append({
                            "date": day,
                            "status": "szk",
                            "status_label": "Sababsiz kelmadi",
                            "first_in": None,
                            "last_out": None,
                            "worked": "0:00",
                            "difference": f"-{minutes_to_hm(shift_min)}",
                            "penalty": penalty_amount,
                            "bonus": 0,
                            "daily_total": -penalty_amount,
                            "att_comment": attendance.comment if attendance else "",
                        })
                    continue

                first_event = events.first()
                last_event = events.last()
                first_in = localtime(first_event.time)
                last_out = localtime(last_event.time)
                worked_min = int((last_out - first_in).total_seconds() / 60)
                worked_min -= break_min

                if worked_min < 0:
                    worked_min = 0

                worked_minutes += worked_min
                minute_salary = day_salary / shift_min if shift_min else 0
                bonus_amount = 0
                penalty_amount = 0
                raw_late_minutes = int((first_in.replace(tzinfo=None) - shift_start).total_seconds() / 60)
                approved_late = emp.shift.approved_late_min or 0
                late_minutes = raw_late_minutes if raw_late_minutes > approved_late else 0
                raw_departure_minutes = int((last_out.replace(tzinfo=None) - shift_end).total_seconds() / 60)
                early_leave_minutes = abs(raw_departure_minutes) if raw_departure_minutes < 0 else 0
                overtime_minutes = max(0, raw_departure_minutes)
                penalty_minutes = late_minutes + early_leave_minutes
                adjustment_minutes = overtime_minutes - penalty_minutes

                if attendance and attendance.status == 'sbk':
                    sbk_count += 1
                    status = "sbk"
                    status_label = "Sababli kelmadi"
                    bonus_amount = 0
                    penalty_amount = 0
                else:
                    status = "worked"
                    status_label = "Ishlagan"
                    if overtime_minutes > 0:
                        bonus_amount = round(overtime_minutes * minute_salary, 2)
                        total_bonus += bonus_amount
                        total_overtime += overtime_minutes

                    if penalty_minutes > 0:
                        total_undertime += penalty_minutes

                        if emp.is_fine:
                            penalty_amount = round(penalty_minutes * minute_salary, 2)

                            if total_penalty + penalty_amount > emp.salary:
                                penalty_amount = max(0, emp.salary - total_penalty)

                            total_penalty += penalty_amount
                
                details.append({
                    "date": day,
                    "status": status,
                    "status_label": status_label,
                    "first_in": first_in.strftime("%H:%M"),
                    "last_out": last_out.strftime("%H:%M"),
                    "worked": minutes_to_hm(worked_min),
                    "difference": (
                        minutes_to_hm(adjustment_minutes)
                        if adjustment_minutes >= 0
                        else f"-{minutes_to_hm(abs(adjustment_minutes))}"
                    ),
                    "penalty": round(penalty_amount, 2),
                    "bonus": round(bonus_amount, 2),
                    "daily_total": round(bonus_amount - penalty_amount, 2),
                    "att_comment": attendance.comment if attendance else ""
                })

            reports.append({
                "employee_id": emp.id,
                "employee_name": emp.name,
                "shift_start_time": shift_start_time,
                "shift_end_time": shift_end_time,
                "year": year,
                "month": month,
                "sbk_count": sbk_count,
                "szk_count": szk_count,
                "worked_time": minutes_to_hm(worked_minutes),
                "total_overtime": minutes_to_hm(total_overtime),
                "total_undertime": minutes_to_hm(total_undertime),
                "total_bonus": int(round(total_bonus)),
                "total_penalty": int(round(total_penalty)),
                "net_adjustment": int(round(total_bonus - total_penalty)),
                "employee_salary": emp.salary,
                "new_salary": emp.salary + (int(round(total_bonus - total_penalty))),
                "details": details
            })

        return {
            "year": year,
            "month": month,
            "count": len(reports),
            "results": reports
        }