from django.contrib import admin


class NameOnlyAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


class SimpleReadAdmin(admin.ModelAdmin):
    list_display = ("id",)
