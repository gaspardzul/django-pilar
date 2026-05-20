from django.urls import path

from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', views.inventory_home, name='home'),

    # Categorías
    path('categories/', views.categories_list, name='categories_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<uuid:category_id>/edit/', views.category_edit, name='category_edit'),
    path('categories/<uuid:category_id>/delete/', views.category_delete, name='category_delete'),

    # Artículos
    path('items/', views.items_list, name='items_list'),
    path('items/export/', views.items_export, name='items_export'),
    path('items/create/', views.item_create, name='item_create'),
    path('items/<uuid:item_id>/', views.item_detail, name='item_detail'),
    path('items/<uuid:item_id>/edit/', views.item_edit, name='item_edit'),
    path('items/<uuid:item_id>/movement/', views.item_add_movement, name='item_add_movement'),
]
