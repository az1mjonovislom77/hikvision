from django.urls import path

from event.api.views import AccessEventListView, EventSyncView

urlpatterns = [path("events-sync/", EventSyncView.as_view()), path("events/", AccessEventListView.as_view())]
