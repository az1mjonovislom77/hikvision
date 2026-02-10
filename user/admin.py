from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .forms import UserAdminCreateForm
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = UserAdminCreateForm
    model = User

    list_display = ("id", "phone_number", "role", "is_staff", "is_active")

    fieldsets = (
        (None, {"fields": ("phone_number", "password")}),
        ("Info", {"fields": ("full_name", "phone_number", "role")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "is_active")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone_number", "password"),
        }),
    )
