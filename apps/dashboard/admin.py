from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _

from .models import (
    Member, Ministry, Family, MemberMinistry, FamilyMember,
    SubscriptionPlan, UserSettings
)


class DashboardAdminSite(AdminSite):
    site_header = _('Dashboard Administration')
    site_title = _('Dashboard Admin')
    index_title = _('Welcome to the Dashboard Admin')

dashboard_admin_site = DashboardAdminSite(name='dashboard_admin')


# Inlines
class MemberMinistryInline(admin.TabularInline):
    model = MemberMinistry
    extra = 1
    fields = ('ministry', 'role', 'start_date', 'end_date')


class FamilyMemberInline(admin.TabularInline):
    model = FamilyMember
    extra = 1
    fields = ('family', 'relationship_type', 'is_primary_contact', 'start_date', 'end_date')


# Member Admin
@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'email', 'phone', 'status', 'join_date', 'get_age')
    list_filter = ('status', 'gender', 'join_date')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    date_hierarchy = 'join_date'
    inlines = [MemberMinistryInline, FamilyMemberInline]
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'gender', 'photo')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'address')
        }),
        ('Membership', {
            'fields': ('join_date', 'status', 'notes')
        }),
    )
    
    def get_age(self, obj):
        age = obj.get_age()
        return f"{age} years" if age else "N/A"
    get_age.short_description = 'Age'


# Ministry Admin
@admin.register(Ministry)
class MinistryAdmin(admin.ModelAdmin):
    list_display = ('name', 'leader', 'active', 'get_member_count', 'created_at')
    list_filter = ('active', 'created_at')
    search_fields = ('name', 'description')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'leader', 'active')
        }),
    )
    
    def get_member_count(self, obj):
        return obj.get_active_members().count()
    get_member_count.short_description = 'Active Members'


# Family Admin
@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ('family_name', 'primary_contact', 'get_member_count', 'created_at')
    search_fields = ('family_name', 'address')
    inlines = [FamilyMemberInline]
    
    fieldsets = (
        (None, {
            'fields': ('family_name', 'primary_contact', 'address', 'notes')
        }),
    )
    
    def get_member_count(self, obj):
        return obj.get_family_members().count()
    get_member_count.short_description = 'Members'


# MemberMinistry Admin
@admin.register(MemberMinistry)
class MemberMinistryAdmin(admin.ModelAdmin):
    list_display = ('member', 'ministry', 'role', 'start_date', 'end_date', 'is_active')
    list_filter = ('role', 'ministry', 'start_date')
    search_fields = ('member__first_name', 'member__last_name', 'ministry__name')
    date_hierarchy = 'start_date'
    
    fieldsets = (
        (None, {
            'fields': ('member', 'ministry', 'role')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date')
        }),
        ('Additional Info', {
            'fields': ('notes',)
        }),
    )


# FamilyMember Admin
@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ('member', 'family', 'relationship_type', 'is_primary_contact', 'is_active_member')
    list_filter = ('relationship_type', 'is_primary_contact', 'family')
    search_fields = ('member__first_name', 'member__last_name', 'family__family_name')
    
    fieldsets = (
        (None, {
            'fields': ('family', 'member', 'relationship_type', 'is_primary_contact')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date')
        }),
        ('Additional Info', {
            'fields': ('notes',)
        }),
    )
