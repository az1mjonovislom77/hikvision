from django.urls import path
from .views import EventSyncView, AccessEventListView

urlpatterns = [
    path("events-sync/", EventSyncView.as_view()),
    path("events/", AccessEventListView.as_view())
]
