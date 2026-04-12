from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from .models import Organization, Domain


@admin.register(Organization)
class OrganizationAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'schema_name', 'created_on', 'subscription_status', 'is_active')
    list_filter = ('subscription_status', 'is_active', 'created_on')
    search_fields = ('name', 'schema_name')


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ('domain', 'tenant', 'is_primary')
    list_filter = ('is_primary',)
    search_fields = ('domain', 'tenant__name')
