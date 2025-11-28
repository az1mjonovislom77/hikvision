from django.urls import path
from .views import AccessEventList, load_hikvision_history, hikvision_webhook

urlpatterns = [
    path("hikvision/load-history/", load_hikvision_history),
    path("hikvision/events/", AccessEventList.as_view()),
    path("hikvision/webhook/", hikvision_webhook)
]
