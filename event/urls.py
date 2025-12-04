from django.urls import path
from .views import AccessEventList

urlpatterns = [
    path("events/", AccessEventList.as_view())
]
