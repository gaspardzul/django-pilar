from django.contrib import admin

from .models import Item, ItemCategory, ItemMovement


@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'get_items_count')
    list_filter = ('active',)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'status', 'condition', 'quantity', 'assigned_to', 'location')
    list_filter = ('status', 'condition', 'category')
    search_fields = ('name', 'code', 'description')


@admin.register(ItemMovement)
class ItemMovementAdmin(admin.ModelAdmin):
    list_display = ('item', 'movement_type', 'member', 'date')
    list_filter = ('movement_type',)
    date_hierarchy = 'date'
