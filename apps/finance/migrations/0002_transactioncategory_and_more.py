import uuid

import django.db.models.deletion
from django.db import migrations, models

INCOME_CATEGORIES = [
    'Diezmo',
    'Ofrenda',
    'Ofrenda Especial',
    'Donación',
    'Ingreso de Evento',
    'Misiones (Ingreso)',
    'Otros Ingresos',
]

EXPENSE_CATEGORIES = [
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

# Map old char values → new category names
CATEGORY_MAP = {
    'tithe': 'Diezmo',
    'offering': 'Ofrenda',
    'special_offering': 'Ofrenda Especial',
    'donation': 'Donación',
    'event_revenue': 'Ingreso de Evento',
    'other_income': 'Otros Ingresos',
    'utilities': 'Servicios (Luz, Agua, Internet)',
    'rent': 'Renta / Hipoteca',
    'salaries': 'Salarios / Honorarios',
    'ministry': 'Gastos de Ministerio',
    'maintenance': 'Mantenimiento',
    'supplies': 'Materiales y Suministros',
    'travel': 'Viajes y Transporte',
    'marketing': 'Publicidad / Marketing',
    'missions': 'Misiones (Egreso)',
    'other_expense': 'Otros Egresos',
    'pledge': 'Otros Ingresos',
}


def seed_and_migrate(apps, schema_editor):
    TransactionCategory = apps.get_model('finance', 'TransactionCategory')
    Transaction = apps.get_model('finance', 'Transaction')
    Contribution = apps.get_model('finance', 'Contribution')

    # Create all default categories
    for i, name in enumerate(INCOME_CATEGORIES):
        TransactionCategory.objects.get_or_create(
            name=name, category_type='income',
            defaults={'is_default': True, 'active': True, 'order': i},
        )
    for i, name in enumerate(EXPENSE_CATEGORIES):
        TransactionCategory.objects.get_or_create(
            name=name, category_type='expense',
            defaults={'is_default': True, 'active': True, 'order': i},
        )

    # Migrate existing transactions: old char → FK
    fallback_income = TransactionCategory.objects.filter(category_type='income').first()
    fallback_expense = TransactionCategory.objects.filter(category_type='expense').first()

    for tx in Transaction.objects.all():
        old_val = tx.category_old or ''
        cat_name = CATEGORY_MAP.get(old_val)
        if cat_name:
            cat = TransactionCategory.objects.filter(name=cat_name).first()
        else:
            cat = None
        if cat is None:
            cat = fallback_income if tx.transaction_type == 'income' else fallback_expense
        tx.category_new = cat
        tx.save(update_fields=['category_new'])

    # Migrate existing contributions: old char → FK
    for contrib in Contribution.objects.all():
        old_val = contrib.contribution_type or ''
        cat_name = CATEGORY_MAP.get(old_val)
        cat = TransactionCategory.objects.filter(name=cat_name).first() if cat_name else None
        if cat is None:
            cat = fallback_income
        contrib.category = cat
        contrib.save(update_fields=['category'])


def unseed_categories(apps, schema_editor):
    TransactionCategory = apps.get_model('finance', 'TransactionCategory')
    TransactionCategory.objects.filter(is_default=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0001_initial'),
    ]

    operations = [
        # 1. Create TransactionCategory table
        migrations.CreateModel(
            name='TransactionCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, verbose_name='Nombre')),
                ('category_type', models.CharField(
                    choices=[('income', 'Ingreso'), ('expense', 'Egreso')],
                    max_length=10, verbose_name='Tipo',
                )),
                ('description', models.CharField(blank=True, max_length=200, verbose_name='Descripción')),
                ('is_default', models.BooleanField(default=False, verbose_name='Categoría predeterminada')),
                ('active', models.BooleanField(default=True, verbose_name='Activa')),
                ('order', models.PositiveSmallIntegerField(default=0, verbose_name='Orden')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Categoría',
                'verbose_name_plural': 'Categorías',
                'db_table': 'finance_transaction_category',
                'ordering': ['category_type', 'order', 'name'],
            },
        ),

        # 2. Rename old category char field on Transaction so we can add the new FK
        migrations.RenameField(
            model_name='transaction',
            old_name='category',
            new_name='category_old',
        ),

        # 3. Add new nullable FK on Transaction
        migrations.AddField(
            model_name='transaction',
            name='category_new',
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='transactions',
                to='finance.transactioncategory',
                verbose_name='Categoría',
            ),
        ),

        # 4. Add nullable category FK on Contribution
        migrations.AddField(
            model_name='contribution',
            name='category',
            field=models.ForeignKey(
                null=True, blank=True,
                limit_choices_to={'category_type': 'income'},
                on_delete=django.db.models.deletion.PROTECT,
                related_name='contributions',
                to='finance.transactioncategory',
                verbose_name='Tipo de contribución',
            ),
        ),

        # 5. Seed categories + migrate existing data
        migrations.RunPython(seed_and_migrate, unseed_categories),

        # 6. Remove old indexes
        migrations.RemoveIndex(model_name='contribution', name='finance_con_contrib_439f7e_idx'),
        migrations.RemoveIndex(model_name='transaction', name='finance_tra_categor_afb10f_idx'),

        # 7. Remove old char fields
        migrations.RemoveField(model_name='transaction', name='category_old'),
        migrations.RemoveField(model_name='contribution', name='contribution_type'),

        # 8. Rename category_new → category on Transaction
        migrations.RenameField(
            model_name='transaction',
            old_name='category_new',
            new_name='category',
        ),

        # 9. Make both FKs non-nullable
        migrations.AlterField(
            model_name='transaction',
            name='category',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='transactions',
                to='finance.transactioncategory',
                verbose_name='Categoría',
            ),
        ),
        migrations.AlterField(
            model_name='contribution',
            name='category',
            field=models.ForeignKey(
                limit_choices_to={'category_type': 'income'},
                on_delete=django.db.models.deletion.PROTECT,
                related_name='contributions',
                to='finance.transactioncategory',
                verbose_name='Tipo de contribución',
            ),
        ),
    ]
