import openpyxl
from django.http import HttpResponse
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter


class AttendanceExcelExportService:

    @staticmethod
    def auto_adjust_column_width(ws):
        for column_cells in ws.columns:
            max_length = 0
            column = column_cells[0].column
            column_letter = get_column_letter(column)

            for cell in column_cells:
                try:
                    if cell.value is not None:
                        cell_length = len(str(cell.value))
                        if cell_length > max_length:
                            max_length = cell_length
                except Exception:
                    pass

            ws.column_dimensions[column_letter].width = max_length + 3

    @staticmethod
    def style_sheet(ws):
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin")
        )

        for row in ws.iter_rows():
            for cell in row:
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = thin_border

        for cell in ws[1]:
            cell.font = Font(bold=True)

    @staticmethod
    def format_number_columns(ws, columns):
        for col in columns:
            for cell in ws[col]:
                if isinstance(cell.value, (int, float)):
                    cell.number_format = '# ##0'

    @staticmethod
    def generate_monthly_excel(report, year, month):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Monthly Report"
        ws.append([
            "ID",
            "Employee",
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
        AttendanceExcelExportService.style_sheet(ws)
        AttendanceExcelExportService.format_number_columns(ws, ["E", "F", "I", "J", "K", "B"])
        for row in range(ws.max_row - 3, ws.max_row + 1):
            cell = ws[f"B{row}"]
            if isinstance(cell.value, (int, float)):
                cell.number_format = '# ##0'

        AttendanceExcelExportService.auto_adjust_column_width(ws)
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

        AttendanceExcelExportService.style_sheet(details_ws)
        AttendanceExcelExportService.format_number_columns(details_ws, ["H", "I", "J"])
        AttendanceExcelExportService.auto_adjust_column_width(details_ws)
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = (
            f'attachment; filename=attendance_{year}_{month}.xlsx')
        wb.save(response)
        return response
