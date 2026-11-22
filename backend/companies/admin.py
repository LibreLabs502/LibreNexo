from django.contrib import admin

from .models import Company, Membership


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    autocomplete_fields = ["user"]


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "tax_id", "is_active"]
    search_fields = ["name", "tax_id"]
    inlines = [MembershipInline]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "company", "role", "is_active"]
    list_filter = ["role", "is_active", "company"]
    search_fields = ["user__username", "company__name"]
    autocomplete_fields = ["user", "company"]
