from django.urls import path, include
from rest_framework.routers import DefaultRouter

from utils.views.views import DevicesViewSet, DepartmentViewSet, BranchViewSet, TelegramChannelViewSet, \
    PlanListView, SubscriptionViewSet

router = DefaultRouter()
router.register('devices', DevicesViewSet)
router.register('departments', DepartmentViewSet)
router.register('branch', BranchViewSet)
router.register('telegramchannel', TelegramChannelViewSet)
router.register('subscription', SubscriptionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path("plans/", PlanListView.as_view(), name="plan-list"),
]
