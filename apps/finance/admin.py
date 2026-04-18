from django.contrib import admin

from .models import Budget, Contribution, FinancialAccount, Transaction, TransactionCategory


@admin.register(TransactionCategory)
class TransactionCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'active', 'is_default', 'order')
    list_filter = ('category_type', 'active', 'is_default')
    search_fields = ('name',)


@admin.register(FinancialAccount)
class FinancialAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_type', 'bank_name', 'current_balance', 'active')
    list_filter = ('account_type', 'active')
    search_fields = ('name', 'bank_name')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'transaction_type', 'category', 'amount', 'account', 'status', 'related_member')
    list_filter = ('transaction_type', 'category', 'status', 'payment_method', 'date')
    search_fields = ('description', 'reference_number', 'related_member__first_name', 'related_member__last_name')
    date_hierarchy = 'date'


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ('member', 'category', 'amount', 'date', 'payment_method', 'receipt_number')
    list_filter = ('category', 'payment_method', 'frequency')
    search_fields = ('member__first_name', 'member__last_name', 'receipt_number')
    date_hierarchy = 'date'


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('name', 'period', 'start_date', 'end_date', 'total_income_budget', 'total_expense_budget')
    list_filter = ('period',)
