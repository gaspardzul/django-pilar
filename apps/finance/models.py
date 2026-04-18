import uuid

from django.db import models
from django.utils import timezone

from apps.business.models import Member


class TransactionCategory(models.Model):
    """Catálogo de categorías financieras, personalizable por iglesia."""

    TYPE_CHOICES = [
        ('income', 'Ingreso'),
        ('expense', 'Egreso'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name='Nombre')
    category_type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name='Tipo')
    description = models.CharField(max_length=200, blank=True, verbose_name='Descripción')
    is_default = models.BooleanField(default=False, verbose_name='Categoría predeterminada')
    active = models.BooleanField(default=True, verbose_name='Activa')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='Orden')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_transaction_category'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['category_type', 'order', 'name']

    def __str__(self):
        return f'{self.name} ({self.get_category_type_display()})'


# Default categories seeded on first use
DEFAULT_INCOME_CATEGORIES = [
    'Diezmo',
    'Ofrenda',
    'Ofrenda Especial',
    'Donación',
    'Ingreso de Evento',
    'Misiones (Ingreso)',
    'Otros Ingresos',
]

DEFAULT_EXPENSE_CATEGORIES = [
    'Servicios (Luz, Agua, Internet)',
    'Renta / Hipoteca',
    'Salarios / Honorarios',
    'Gastos de Ministerio',
    'Mantenimiento',
    'Materiales y Suministros',
    'Viajes y Transporte',
    'Publicidad / Marketing',
    'Misiones (Egreso)',
    'Otros Egresos',
]


class FinancialAccount(models.Model):
    """Cuentas bancarias o cajas de la iglesia."""

    ACCOUNT_TYPE_CHOICES = [
        ('cash', 'Efectivo / Caja'),
        ('checking', 'Cuenta Corriente'),
        ('savings', 'Cuenta de Ahorro'),
        ('investment', 'Inversión'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name='Nombre')
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, verbose_name='Tipo')
    bank_name = models.CharField(max_length=100, blank=True, verbose_name='Banco')
    account_number = models.CharField(max_length=50, blank=True, verbose_name='Número de cuenta')
    initial_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Saldo inicial')
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Saldo actual')
    active = models.BooleanField(default=True, verbose_name='Activa')
    notes = models.TextField(blank=True, verbose_name='Notas')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_account'
        verbose_name = 'Cuenta Financiera'
        verbose_name_plural = 'Cuentas Financieras'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.get_account_type_display()})'

    def recalculate_balance(self):
        from django.db.models import Sum
        income = self.transactions.filter(transaction_type='income', status='completed').aggregate(total=Sum('amount'))['total'] or 0
        expense = self.transactions.filter(transaction_type='expense', status='completed').aggregate(total=Sum('amount'))['total'] or 0
        self.current_balance = self.initial_balance + income - expense
        self.save(update_fields=['current_balance'])
        return self.current_balance


class Transaction(models.Model):
    """Movimiento financiero: ingreso o egreso."""

    TRANSACTION_TYPE_CHOICES = [
        ('income', 'Ingreso'),
        ('expense', 'Egreso'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Efectivo'),
        ('bank_transfer', 'Transferencia Bancaria'),
        ('check', 'Cheque'),
        ('digital', 'Pago Digital'),
        ('card', 'Tarjeta'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES, verbose_name='Tipo')
    category = models.ForeignKey(
        TransactionCategory,
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name='Categoría',
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Monto')
    description = models.CharField(max_length=300, verbose_name='Descripción')
    date = models.DateField(verbose_name='Fecha')
    account = models.ForeignKey(FinancialAccount, on_delete=models.PROTECT, related_name='transactions', verbose_name='Cuenta')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash', verbose_name='Método de pago')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed', verbose_name='Estado')
    reference_number = models.CharField(max_length=100, blank=True, verbose_name='Número de referencia')
    related_member = models.ForeignKey(
        Member, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions', verbose_name='Miembro relacionado'
    )
    notes = models.TextField(blank=True, verbose_name='Notas')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_transaction'
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['transaction_type', 'date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.get_transaction_type_display()} - {self.category.name} ${self.amount}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.account.recalculate_balance()


class Contribution(models.Model):
    """Registro de diezmos y ofrendas por miembro."""

    FREQUENCY_CHOICES = [
        ('weekly', 'Semanal'),
        ('biweekly', 'Quincenal'),
        ('monthly', 'Mensual'),
        ('one_time', 'Única vez'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='contributions', verbose_name='Miembro')
    category = models.ForeignKey(
        TransactionCategory,
        on_delete=models.PROTECT,
        related_name='contributions',
        verbose_name='Tipo de contribución',
        limit_choices_to={'category_type': 'income'},
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto')
    date = models.DateField(default=timezone.now, verbose_name='Fecha')
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='one_time', verbose_name='Frecuencia')
    payment_method = models.CharField(
        max_length=20, choices=Transaction.PAYMENT_METHOD_CHOICES, default='cash', verbose_name='Método de pago'
    )
    receipt_number = models.CharField(max_length=100, blank=True, verbose_name='Número de recibo')
    transaction = models.OneToOneField(
        Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='contribution', verbose_name='Transacción'
    )
    notes = models.TextField(blank=True, verbose_name='Notas')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_contribution'
        verbose_name = 'Contribución'
        verbose_name_plural = 'Contribuciones'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['member', 'date']),
        ]

    def __str__(self):
        return f'{self.member.get_full_name()} - {self.category.name} ${self.amount} ({self.date})'


class Budget(models.Model):
    """Presupuesto anual o mensual de la iglesia."""

    PERIOD_CHOICES = [
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('annual', 'Anual'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name='Nombre')
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='annual', verbose_name='Período')
    start_date = models.DateField(verbose_name='Fecha inicio')
    end_date = models.DateField(verbose_name='Fecha fin')
    total_income_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Presupuesto de ingresos')
    total_expense_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Presupuesto de egresos')
    notes = models.TextField(blank=True, verbose_name='Notas')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_budget'
        verbose_name = 'Presupuesto'
        verbose_name_plural = 'Presupuestos'
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.name} ({self.start_date.year})'

    def get_actual_income(self):
        from django.db.models import Sum
        return Transaction.objects.filter(
            transaction_type='income', status='completed', date__range=[self.start_date, self.end_date]
        ).aggregate(total=Sum('amount'))['total'] or 0

    def get_actual_expense(self):
        from django.db.models import Sum
        return Transaction.objects.filter(
            transaction_type='expense', status='completed', date__range=[self.start_date, self.end_date]
        ).aggregate(total=Sum('amount'))['total'] or 0

    def get_income_variance(self):
        return self.get_actual_income() - self.total_income_budget

    def get_expense_variance(self):
        return self.total_expense_budget - self.get_actual_expense()
