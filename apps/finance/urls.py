from django.urls import path

from . import views

app_name = 'finance'

urlpatterns = [
    # Dashboard financiero
    path('', views.finance_home, name='home'),

    # Catálogos
    path('catalogs/', views.catalogs, name='catalogs'),
    path('catalogs/categories/create/', views.category_create, name='category_create'),
    path('catalogs/categories/<uuid:category_id>/edit/', views.category_edit, name='category_edit'),
    path('catalogs/categories/<uuid:category_id>/delete/', views.category_delete, name='category_delete'),

    # Cuentas
    path('accounts/', views.accounts_list, name='accounts_list'),
    path('accounts/create/', views.account_create, name='account_create'),
    path('accounts/<uuid:account_id>/', views.account_detail, name='account_detail'),
    path('accounts/<uuid:account_id>/edit/', views.account_edit, name='account_edit'),

    # Transacciones
    path('transactions/', views.transactions_list, name='transactions_list'),
    path('transactions/create/', views.transaction_create, name='transaction_create'),
    path('transactions/<uuid:transaction_id>/', views.transaction_detail, name='transaction_detail'),
    path('transactions/<uuid:transaction_id>/edit/', views.transaction_edit, name='transaction_edit'),
    path('transactions/<uuid:transaction_id>/delete/', views.transaction_delete, name='transaction_delete'),

    # Contribuciones (diezmos y ofrendas)
    path('contributions/', views.contributions_list, name='contributions_list'),
    path('contributions/create/', views.contribution_create, name='contribution_create'),
    path('contributions/<uuid:contribution_id>/edit/', views.contribution_edit, name='contribution_edit'),
    path('contributions/<uuid:contribution_id>/delete/', views.contribution_delete, name='contribution_delete'),

    # Presupuestos
    path('budgets/', views.budgets_list, name='budgets_list'),
    path('budgets/create/', views.budget_create, name='budget_create'),
    path('budgets/<uuid:budget_id>/', views.budget_detail, name='budget_detail'),
    path('budgets/<uuid:budget_id>/edit/', views.budget_edit, name='budget_edit'),
]
