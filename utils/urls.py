from django.urls import path, include
from rest_framework.routers import DefaultRouter

from utils.views.views import DevicesViewSet, DepartmentViewSet, BranchViewSet, TelegramChannelViewSet

router = DefaultRouter()
router.register('devices', DevicesViewSet)
router.register('departments', DepartmentViewSet)
router.register('branch', BranchViewSet)
router.register('telegramchannel', TelegramChannelViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
