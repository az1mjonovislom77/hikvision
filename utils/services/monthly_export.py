import openpyxl
from django.http import HttpResponse


class AttendanceExcelExportService:

    @staticmethod
    def generate_monthly_excel(report, year, month):
        wb = openpyxl.Workbook()

        ws = wb.active
        ws.title = "Monthly Report"

        ws.append([
            "ID",
            "Employee Name",
            "Work Time",
            "Shift",
            "Salary",
            "New Salary",
            "Sababli kelmadi",
            "Sababsiz kelmadi",
            "Bonus",
            "Penalty",
            "Net Adjustment"
        ])

        total_salary = 0
        total_bonus = 0
        total_penalty = 0

        for row in report["results"]:
            total_salary += row["employee_salary"]
            total_bonus += row["total_bonus"]
            total_penalty += row["total_penalty"]

            ws.append([
                row["employee_id"],
                row["employee_name"],
                row["worked_time"],
                f'{row["shift_start_time"]} - {row["shift_end_time"]}',
                row["employee_salary"],
                row["new_salary"],
                row["sbk_count"],
                row["szk_count"],
                row["total_bonus"],
                row["total_penalty"],
                row["net_adjustment"],
            ])

        ws.append([])
        ws.append(["Jami hodimlar", report["count"]])
        ws.append(["Umumiy maosh", total_salary])
        ws.append(["Jami bonus", total_bonus])
        ws.append(["Jami jarima", total_penalty])

        # ================= DETAILS SHEET =================
        details_ws = wb.create_sheet("Daily Details")

        details_ws.append([
            "Employee",
            "Date",
            "Status",
            "First In",
            "Last Out",
            "Worked",
            "Difference",
            "Penalty",
            "Bonus",
            "Daily Total"
        ])

        for emp in report["results"]:
            for detail in emp["details"]:
                details_ws.append([
                    emp["employee_name"],
                    detail.get("date"),
                    detail.get("status_label"),
                    detail.get("first_in"),
                    detail.get("last_out"),
                    detail.get("worked"),
                    detail.get("difference"),
                    detail.get("penalty"),
                    detail.get("bonus"),
                    detail.get("daily_total"),
                ])

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        response["Content-Disposition"] = (
            f'attachment; filename=attendance_{year}_{month}.xlsx'
        )

        wb.save(response)
        return response