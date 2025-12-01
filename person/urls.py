from django.urls import path
from .views import FullSyncPersonsView, PersonCreateView, PersonUpdateView, PersonDeleteView

urlpatterns = [
    path("sync-persons/", FullSyncPersonsView.as_view(), name="sync-persons"),
    path("create/", PersonCreateView.as_view(), name="person_create"),
    path("update/<str:employee_no>/", PersonUpdateView.as_view(), name="person-update"),
    path("delete/<str:employee_no>/", PersonDeleteView.as_view(), name="person-delete"),
]
