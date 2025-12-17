from django.urls import path
from .views.daily_views import DailyAccessListView, DailyAccessExcelExport
from .views.employee_views import FullSyncEmployeesView, EmployeeDetailView, EmployeeCreateView, EmployeeUpdateView, \
    EmployeeDeleteView

urlpatterns = [
    path("sync-employees/", FullSyncEmployeesView.as_view(), name="sync-persons"),
    path("sync-employees/<int:employee_id>/", EmployeeDetailView.as_view(), name="employee-detail"),
    path("create/", EmployeeCreateView.as_view(), name="person_create"),
    path("update/<int:employee_id>/", EmployeeUpdateView.as_view(), name="person-update"),
    path("delete/<int:employee_id>/", EmployeeDeleteView.as_view(), name="person-delete"),
    path("daily-list/", DailyAccessListView.as_view(), name="daily-list"),
    path('daily-excel/', DailyAccessExcelExport.as_view()),

]
