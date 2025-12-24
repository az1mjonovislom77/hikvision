from django.contrib import admin

from utils.models import Devices, Branch, Department, TelegramChannel, Plan, Subscription


@admin.register(Devices)
class DevicesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(TelegramChannel)
class TelegramChannelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'chat_id')


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'plan', 'is_paid')
