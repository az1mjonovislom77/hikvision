from django.contrib import admin

from utils.models import Devices, Branch, Department, TelegramChannel


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
