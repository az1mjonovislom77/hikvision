from django.urls import path
from .views import AbsentEmployeesView, MonthlyAttendanceReportView

urlpatterns = [
    path("absent/", AbsentEmployeesView.as_view()),
    path("report/monthly/", MonthlyAttendanceReportView.as_view()),
]
