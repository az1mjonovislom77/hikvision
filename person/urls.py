from django.urls import path
from .views import FullSyncEmployeesView, EmployeeCreateView, EmployeeUpdateView, EmployeeDeleteView, \
    DailyAccessListView, DailyAccessExcelExport

urlpatterns = [
    path("sync-employees/", FullSyncEmployeesView.as_view(), name="sync-persons"),
    path("create/", EmployeeCreateView.as_view(), name="person_create"),
    path("update/<str:employee_no>/", EmployeeUpdateView.as_view(), name="person-update"),
    path("delete/<str:employee_no>/", EmployeeDeleteView.as_view(), name="person-delete"),
    path("daily-list/", DailyAccessListView.as_view(), name="daily-list"),
    path('daily-excel/', DailyAccessExcelExport.as_view()),

]
