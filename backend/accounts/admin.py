from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("LibreNexo", {"fields": ("full_name", "created_at", "updated_at")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("LibreNexo", {"fields": ("full_name", "email")}),
    )
    readonly_fields = ("created_at", "updated_at")
