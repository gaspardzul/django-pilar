from django.contrib import admin

from .models import (
    Member, Ministry, Family, MemberMinistry, FamilyMember,
    Event, EventWorkGroup, EventWorker,
    EventBudget, EventIncome, EventExpense
)


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
    list_display = ('get_full_name', 'email', 'phone', 'status', 'is_baptized', 'baptism_date', 'join_date', 'get_age')
    list_filter = ('status', 'gender', 'is_baptized', 'join_date', 'baptism_date')
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
        ('Baptism Information', {
            'fields': ('is_baptized', 'baptism_date', 'baptism_place', 'baptized_by')
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


# Event Inlines
class EventWorkGroupInline(admin.TabularInline):
    model = EventWorkGroup
    extra = 1
    fields = ('name', 'group_type', 'coordinator', 'required_workers')


class EventIncomeInline(admin.TabularInline):
    model = EventIncome
    extra = 0
    fields = ('amount', 'source', 'donor', 'date', 'description')


class EventExpenseInline(admin.TabularInline):
    model = EventExpense
    extra = 0
    fields = ('amount', 'category', 'vendor', 'date', 'status')


class EventWorkerInline(admin.TabularInline):
    model = EventWorker
    extra = 1
    fields = ('member', 'status', 'role')


# Event Admin
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'event_type', 'start_date', 'location', 'status', 'is_free_entry', 'get_total_workers')
    list_filter = ('status', 'event_type', 'is_free_entry', 'start_date')
    search_fields = ('name', 'description', 'location')
    date_hierarchy = 'start_date'
    inlines = [EventWorkGroupInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'description', 'event_type', 'status')
        }),
        ('Fecha y Lugar', {
            'fields': ('start_date', 'end_date', 'location')
        }),
        ('Entrada', {
            'fields': ('is_free_entry', 'ticket_price', 'max_capacity')
        }),
        ('Organización', {
            'fields': ('organizer', 'notes')
        }),
    )


# EventWorkGroup Admin
@admin.register(EventWorkGroup)
class EventWorkGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'group_type', 'coordinator', 'required_workers', 'get_workers_count', 'is_fully_staffed')
    list_filter = ('group_type', 'event')
    search_fields = ('name', 'description', 'event__name')
    inlines = [EventWorkerInline]
    
    fieldsets = (
        (None, {
            'fields': ('event', 'name', 'group_type', 'description')
        }),
        ('Coordinación', {
            'fields': ('coordinator', 'required_workers')
        }),
        ('Notas', {
            'fields': ('notes',)
        }),
    )


# EventWorker Admin
@admin.register(EventWorker)
class EventWorkerAdmin(admin.ModelAdmin):
    list_display = ('member', 'work_group', 'get_event', 'status', 'role', 'assigned_at')
    list_filter = ('status', 'work_group__group_type', 'assigned_at')
    search_fields = ('member__first_name', 'member__last_name', 'work_group__name', 'work_group__event__name')
    date_hierarchy = 'assigned_at'
    
    fieldsets = (
        (None, {
            'fields': ('work_group', 'member', 'status', 'role')
        }),
        ('Notas', {
            'fields': ('notes',)
        }),
    )
    
    def get_event(self, obj):
        return obj.work_group.event.name
    get_event.short_description = 'Event'


# EventBudget Admin
@admin.register(EventBudget)
class EventBudgetAdmin(admin.ModelAdmin):
    list_display = ('event', 'total_budget', 'get_total_income', 'get_total_expenses', 'get_balance')
    search_fields = ('event__name',)
    inlines = [EventIncomeInline, EventExpenseInline]
    
    fieldsets = (
        (None, {
            'fields': ('event', 'total_budget', 'target_budget')
        }),
        ('Notas', {
            'fields': ('notes',)
        }),
    )
    
    def get_total_income(self, obj):
        return f"${obj.get_total_income():,.2f}"
    get_total_income.short_description = 'Total Ingresos'
    
    def get_total_expenses(self, obj):
        return f"${obj.get_total_expenses():,.2f}"
    get_total_expenses.short_description = 'Total Egresos'
    
    def get_balance(self, obj):
        balance = obj.get_balance()
        return f"${balance:,.2f}"
    get_balance.short_description = 'Balance'


# EventIncome Admin
@admin.register(EventIncome)
class EventIncomeAdmin(admin.ModelAdmin):
    list_display = ('get_event', 'amount', 'source', 'donor', 'date', 'description')
    list_filter = ('source', 'date', 'budget__event')
    search_fields = ('description', 'donor__first_name', 'donor__last_name', 'budget__event__name')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('budget', 'amount', 'source', 'description')
        }),
        ('Donante', {
            'fields': ('donor', 'date', 'receipt_number')
        }),
        ('Notas', {
            'fields': ('notes',)
        }),
    )
    
    def get_event(self, obj):
        return obj.budget.event.name
    get_event.short_description = 'Event'


# EventExpense Admin
@admin.register(EventExpense)
class EventExpenseAdmin(admin.ModelAdmin):
    list_display = ('get_event', 'amount', 'category', 'vendor', 'date', 'status', 'paid_by')
    list_filter = ('category', 'status', 'date', 'budget__event')
    search_fields = ('description', 'vendor', 'budget__event__name', 'paid_by__first_name', 'paid_by__last_name')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('budget', 'amount', 'category', 'description')
        }),
        ('Detalles', {
            'fields': ('vendor', 'date', 'invoice_number', 'status')
        }),
        ('Pago', {
            'fields': ('paid_by',)
        }),
        ('Notas', {
            'fields': ('notes',)
        }),
    )
    
    def get_event(self, obj):
        return obj.budget.event.name
    get_event.short_description = 'Event'
