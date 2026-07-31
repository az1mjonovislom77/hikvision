from django.urls import path

from person.api.views.daily_views import DailyAccessExcelExport, DailyAccessListView
from person.api.views.employee_views import (
    EmployeeCreateView,
    EmployeeDeleteView,
    EmployeeDetailView,
    EmployeeHistoryListView,
    EmployeeListView,
    EmployeeSyncView,
    EmployeeUpdateView,
)

urlpatterns = [
    path("sync-employees/", EmployeeSyncView.as_view(), name="sync-persons"),
    path("employees/", EmployeeListView.as_view(), name="persons"),
    path("employee-history/", EmployeeHistoryListView.as_view(), name="employee-history"),
    path("employee-detail/<int:employee_id>/", EmployeeDetailView.as_view(), name="employee-detail"),
    path("create/", EmployeeCreateView.as_view(), name="person_create"),
    path("update/<int:employee_id>/", EmployeeUpdateView.as_view(), name="person-update"),
    path("delete/<int:employee_id>/", EmployeeDeleteView.as_view(), name="person-delete"),
    path("daily-list/", DailyAccessListView.as_view(), name="daily-list"),
    path("daily-excel/", DailyAccessExcelExport.as_view()),
]
