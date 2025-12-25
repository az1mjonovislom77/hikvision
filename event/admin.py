from django.contrib import admin
from event.models import AccessEvent
from utils.base.admin_base import NameOnlyAdmin


@admin.register(AccessEvent)
class AccessEventAdmin(NameOnlyAdmin):
    pass
