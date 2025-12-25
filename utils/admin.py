from django.contrib import admin
from utils.base.admin_base import NameOnlyAdmin
from utils.models import Devices, Branch, Department, TelegramChannel, Plan, Subscription, Notification


@admin.register(Devices)
class DevicesAdmin(NameOnlyAdmin):
    pass


@admin.register(Department)
class DepartmentAdmin(NameOnlyAdmin):
    pass


@admin.register(Branch)
class BranchAdmin(NameOnlyAdmin):
    pass


@admin.register(TelegramChannel)
class TelegramChannelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'chat_id')


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'plan', 'is_paid')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'text')
