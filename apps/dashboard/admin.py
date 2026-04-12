from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _

from .models import SubscriptionPlan, UserSettings


class DashboardAdminSite(AdminSite):
    site_header = _('Dashboard Administration')
    site_title = _('Dashboard Admin')
    index_title = _('Welcome to the Dashboard Admin')


dashboard_admin_site = DashboardAdminSite(name='dashboard_admin')


# SubscriptionPlan Admin
@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'interval', 'is_active', 'created_at')
    list_filter = ('interval', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'price', 'interval')
        }),
        ('Features', {
            'fields': ('features',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


# UserSettings Admin
@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_plan', 'subscription_status', 'get_subscription_display')
    list_filter = ('subscription_status', 'subscription_plan')
    search_fields = ('user__email',)
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Notifications', {
            'fields': ('notify_comments', 'notify_updates', 'notify_marketing')
        }),
        ('API', {
            'fields': ('api_key', 'api_key_created_at')
        }),
        ('Subscription', {
            'fields': ('subscription_plan', 'subscription_status', 'subscription_start_date', 'subscription_end_date', 'trial_end_date')
        }),
    )
    
    readonly_fields = ('api_key_created_at',)
