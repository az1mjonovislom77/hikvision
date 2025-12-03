from django.urls import path, include
from .views.person_views import FullSyncPersonsView, PersonCreateView, PersonUpdateView, PersonDeleteView
from rest_framework.routers import DefaultRouter

from .views.staff_views import StaffViewSet, DailyAccessListView

router = DefaultRouter()
router.register('staff', StaffViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path("sync-persons/", FullSyncPersonsView.as_view(), name="sync-persons"),
    path("create/", PersonCreateView.as_view(), name="person_create"),
    path("update/<str:employee_no>/", PersonUpdateView.as_view(), name="person-update"),
    path("delete/<str:employee_no>/", PersonDeleteView.as_view(), name="person-delete"),
    path("daily-list/", DailyAccessListView.as_view(), name="daily-list"),
]
