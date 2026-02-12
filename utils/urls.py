from django.urls import path, include
from rest_framework.routers import DefaultRouter
from utils.views import DevicesViewSet, DepartmentViewSet, BranchViewSet, TelegramChannelViewSet, \
    SubscriptionViewSet, PlanViewSet, NotificationViewSet, AdminNotificationViewSet, SmartCityAPIView

router = DefaultRouter()
router.register('devices', DevicesViewSet)
router.register('departments', DepartmentViewSet)
router.register('branch', BranchViewSet)
router.register('telegramchannel', TelegramChannelViewSet)
router.register('subscription', SubscriptionViewSet)
router.register('plan', PlanViewSet)
router.register('notification', NotificationViewSet)
router.register("admin/notification", AdminNotificationViewSet, basename="admin-notification")

urlpatterns = [
    path('', include(router.urls)),
    path('smartcity_stats/', SmartCityAPIView.as_view(), name="smart-city-stats")
]
