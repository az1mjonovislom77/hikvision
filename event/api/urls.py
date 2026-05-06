from django.urls import path
from event.api.views import EventSyncView, AccessEventListView

urlpatterns = [
    path("events-sync/", EventSyncView.as_view()),
    path("events/", AccessEventListView.as_view())
]
