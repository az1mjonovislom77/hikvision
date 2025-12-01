from django.urls import path
from .views import AccessEventList, hikvision_webhook

urlpatterns = [
    path("events/", AccessEventList.as_view()),
    path("webhook/", hikvision_webhook)
]
