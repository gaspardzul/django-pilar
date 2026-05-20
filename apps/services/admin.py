from django.contrib import admin

from .models import EligibleMember, ServiceAssignment, ServicePart, ServiceSchedule, ServiceType


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'default_weekdays', 'default_start_time', 'active', 'order')
    list_filter = ('active',)


@admin.register(ServicePart)
class ServicePartAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_type', 'duration_minutes', 'max_participants', 'order')
    list_filter = ('service_type',)


@admin.register(EligibleMember)
class EligibleMemberAdmin(admin.ModelAdmin):
    list_display = ('member', 'service_part')
    list_filter = ('service_part__service_type', 'service_part')


@admin.register(ServiceSchedule)
class ServiceScheduleAdmin(admin.ModelAdmin):
    list_display = ('get_display_title', 'service_type', 'date', 'start_time', 'is_cancelled')
    list_filter = ('service_type', 'is_cancelled')
    date_hierarchy = 'date'


@admin.register(ServiceAssignment)
class ServiceAssignmentAdmin(admin.ModelAdmin):
    list_display = ('member', 'service_part', 'schedule', 'role', 'confirmed')
    list_filter = ('service_part', 'role', 'confirmed')
