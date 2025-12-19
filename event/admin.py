from django.contrib import admin
from event.models import AccessEvent


@admin.register(AccessEvent)
class AccessEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
