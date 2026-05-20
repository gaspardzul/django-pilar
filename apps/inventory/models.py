import uuid

from django.db import models
from django.utils import timezone

from apps.business.models import Member


class ItemCategory(models.Model):
    """Categoría de inventario (Sonido, Mobiliario, Instrumentos, etc.)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name='Nombre')
    description = models.CharField(max_length=200, blank=True, verbose_name='Descripción')
    icon = models.CharField(max_length=50, blank=True, verbose_name='Ícono', help_text='Clase de FontAwesome, ej: fa-microphone')
    active = models.BooleanField(default=True, verbose_name='Activa')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inventory_category'
        verbose_name = 'Categoría de Inventario'
        verbose_name_plural = 'Categorías de Inventario'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_items_count(self):
        return self.items.count()


class Item(models.Model):
    """Artículo del inventario de la iglesia."""

    CONDITION_CHOICES = [
        ('new', 'Nuevo'),
        ('good', 'Bueno'),
        ('fair', 'Regular'),
        ('poor', 'Malo'),
        ('damaged', 'Dañado'),
        ('retired', 'Dado de baja'),
    ]

    STATUS_CHOICES = [
        ('available', 'Disponible'),
        ('in_use', 'En uso'),
        ('lent', 'Prestado'),
        ('maintenance', 'En mantenimiento'),
        ('lost', 'Extraviado'),
        ('retired', 'Dado de baja'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')
    category = models.ForeignKey(ItemCategory, on_delete=models.PROTECT, related_name='items', verbose_name='Categoría')
    code = models.CharField(max_length=50, blank=True, verbose_name='Código / Serie', help_text='Número de serie o código interno')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Cantidad')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good', verbose_name='Condición')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available', verbose_name='Estado')
    location = models.CharField(max_length=200, blank=True, verbose_name='Ubicación', help_text='Dónde se guarda normalmente')
    purchase_date = models.DateField(null=True, blank=True, verbose_name='Fecha de compra')
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Precio de compra')
    assigned_to = models.ForeignKey(
        Member, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_items', verbose_name='Responsable actual',
    )
    photo = models.ImageField(upload_to='inventory/', blank=True, null=True, verbose_name='Foto')
    notes = models.TextField(blank=True, verbose_name='Notas')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inventory_item'
        verbose_name = 'Artículo'
        verbose_name_plural = 'Artículos'
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f'{self.name} ({self.get_status_display()})'

    def is_available(self):
        return self.status == 'available'


class ItemMovement(models.Model):
    """Historial de movimientos: préstamos, devoluciones, mantenimiento."""

    MOVEMENT_TYPES = [
        ('checkout', 'Préstamo / Salida'),
        ('return', 'Devolución'),
        ('maintenance', 'Enviado a mantenimiento'),
        ('maintenance_done', 'Regresó de mantenimiento'),
        ('transfer', 'Transferencia'),
        ('lost', 'Reportado extraviado'),
        ('found', 'Recuperado'),
        ('retired', 'Dado de baja'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='movements', verbose_name='Artículo')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES, verbose_name='Tipo de movimiento')
    member = models.ForeignKey(
        Member, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='item_movements', verbose_name='Miembro involucrado',
    )
    date = models.DateTimeField(default=timezone.now, verbose_name='Fecha')
    expected_return_date = models.DateField(null=True, blank=True, verbose_name='Fecha esperada de devolución')
    notes = models.TextField(blank=True, verbose_name='Notas')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inventory_movement'
        verbose_name = 'Movimiento'
        verbose_name_plural = 'Movimientos'
        ordering = ['-date']

    def __str__(self):
        return f'{self.get_movement_type_display()} - {self.item.name}'
