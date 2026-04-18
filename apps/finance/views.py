from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.business.models import Member

from .models import (
    Budget, Contribution, FinancialAccount,
    Transaction, TransactionCategory,
    DEFAULT_INCOME_CATEGORIES, DEFAULT_EXPENSE_CATEGORIES,
)


def _ensure_categories():
    """Crea categorías por defecto si el tenant no tiene ninguna."""
    if not TransactionCategory.objects.exists():
        for i, name in enumerate(DEFAULT_INCOME_CATEGORIES):
            TransactionCategory.objects.get_or_create(
                name=name, category_type='income',
                defaults={'is_default': True, 'active': True, 'order': i},
            )
        for i, name in enumerate(DEFAULT_EXPENSE_CATEGORIES):
            TransactionCategory.objects.get_or_create(
                name=name, category_type='expense',
                defaults={'is_default': True, 'active': True, 'order': i},
            )


# ── Dashboard ─────────────────────────────────────────────────────────────────

@login_required
@require_http_methods(['GET'])
def finance_home(request):
    _ensure_categories()
    today = timezone.now().date()
    first_day = today.replace(day=1)

    monthly_income = (
        Transaction.objects.filter(transaction_type='income', status='completed', date__gte=first_day, date__lte=today)
        .aggregate(total=Sum('amount'))['total'] or 0
    )
    monthly_expense = (
        Transaction.objects.filter(transaction_type='expense', status='completed', date__gte=first_day, date__lte=today)
        .aggregate(total=Sum('amount'))['total'] or 0
    )
    total_balance = FinancialAccount.objects.filter(active=True).aggregate(total=Sum('current_balance'))['total'] or 0
    monthly_contributions = (
        Contribution.objects.filter(date__gte=first_day, date__lte=today).aggregate(total=Sum('amount'))['total'] or 0
    )
    recent_transactions = Transaction.objects.select_related('account', 'related_member', 'category').order_by('-date', '-created_at')[:5]
    income_by_category = (
        Transaction.objects.filter(transaction_type='income', status='completed', date__gte=first_day, date__lte=today)
        .values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    context = {
        'monthly_income': monthly_income,
        'monthly_expense': monthly_expense,
        'monthly_balance': monthly_income - monthly_expense,
        'total_balance': total_balance,
        'monthly_contributions': monthly_contributions,
        'recent_transactions': recent_transactions,
        'income_by_category': income_by_category,
        'accounts': FinancialAccount.objects.filter(active=True),
    }
    return render(request, 'finance/home.html', context)


# ── Catálogos ─────────────────────────────────────────────────────────────────

@login_required
@require_http_methods(['GET'])
def catalogs(request):
    _ensure_categories()
    income_categories = TransactionCategory.objects.filter(category_type='income').order_by('order', 'name')
    expense_categories = TransactionCategory.objects.filter(category_type='expense').order_by('order', 'name')
    context = {
        'income_categories': income_categories,
        'expense_categories': expense_categories,
    }
    return render(request, 'finance/catalogs/index.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def category_create(request):
    if request.method == 'POST':
        TransactionCategory.objects.create(
            name=request.POST.get('name'),
            category_type=request.POST.get('category_type'),
            description=request.POST.get('description', ''),
            active=True,
        )
        messages.success(request, 'Categoría creada exitosamente.')
        return redirect('finance:catalogs')
    return render(request, 'finance/catalogs/category_form.html', {'action': 'Crear'})


@login_required
@require_http_methods(['GET', 'POST'])
def category_edit(request, category_id):
    category = get_object_or_404(TransactionCategory, id=category_id)
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.category_type = request.POST.get('category_type')
        category.description = request.POST.get('description', '')
        category.active = request.POST.get('active') == 'on'
        category.is_default = request.POST.get('is_default') == 'on'
        category.save()
        messages.success(request, f'Categoría "{category.name}" actualizada.')
        return redirect('finance:catalogs')
    return render(request, 'finance/catalogs/category_form.html', {'category': category, 'action': 'Editar'})


@login_required
@require_http_methods(['POST'])
def category_delete(request, category_id):
    category = get_object_or_404(TransactionCategory, id=category_id)
    if category.transactions.exists() or category.contributions.exists():
        messages.error(request, f'No se puede eliminar "{category.name}" porque tiene transacciones asociadas.')
        return redirect('finance:catalogs')
    category.delete()
    messages.success(request, f'Categoría "{category.name}" eliminada.')
    return redirect('finance:catalogs')


# ── Cuentas ───────────────────────────────────────────────────────────────────

@login_required
@require_http_methods(['GET'])
def accounts_list(request):
    accounts = FinancialAccount.objects.all().order_by('name')
    total_balance = accounts.filter(active=True).aggregate(total=Sum('current_balance'))['total'] or 0
    return render(request, 'finance/accounts/list.html', {'accounts': accounts, 'total_balance': total_balance})


@login_required
@require_http_methods(['GET', 'POST'])
def account_create(request):
    if request.method == 'POST':
        account = FinancialAccount.objects.create(
            name=request.POST.get('name'),
            account_type=request.POST.get('account_type'),
            bank_name=request.POST.get('bank_name', ''),
            account_number=request.POST.get('account_number', ''),
            initial_balance=request.POST.get('initial_balance') or 0,
            notes=request.POST.get('notes', ''),
        )
        account.current_balance = account.initial_balance
        account.save()
        messages.success(request, f'Cuenta "{account.name}" creada exitosamente.')
        return redirect('finance:accounts_list')
    return render(request, 'finance/accounts/form.html', {'action': 'Crear'})


@login_required
@require_http_methods(['GET'])
def account_detail(request, account_id):
    account = get_object_or_404(FinancialAccount, id=account_id)
    transactions = account.transactions.select_related('related_member', 'category').order_by('-date', '-created_at')[:20]
    return render(request, 'finance/accounts/detail.html', {'account': account, 'transactions': transactions})


@login_required
@require_http_methods(['GET', 'POST'])
def account_edit(request, account_id):
    account = get_object_or_404(FinancialAccount, id=account_id)
    if request.method == 'POST':
        account.name = request.POST.get('name')
        account.account_type = request.POST.get('account_type')
        account.bank_name = request.POST.get('bank_name', '')
        account.account_number = request.POST.get('account_number', '')
        account.notes = request.POST.get('notes', '')
        account.active = request.POST.get('active') == 'on'
        account.save()
        messages.success(request, f'Cuenta "{account.name}" actualizada.')
        return redirect('finance:accounts_list')
    return render(request, 'finance/accounts/form.html', {'account': account, 'action': 'Editar'})


# ── Transacciones ─────────────────────────────────────────────────────────────

@login_required
@require_http_methods(['GET'])
def transactions_list(request):
    transactions = Transaction.objects.select_related('account', 'related_member', 'category').order_by('-date', '-created_at')

    type_filter = request.GET.get('type')
    if type_filter:
        transactions = transactions.filter(transaction_type=type_filter)

    category_filter = request.GET.get('category')
    if category_filter:
        transactions = transactions.filter(category_id=category_filter)

    account_filter = request.GET.get('account')
    if account_filter:
        transactions = transactions.filter(account_id=account_filter)

    search = request.GET.get('q', '').strip()
    if search:
        transactions = transactions.filter(
            Q(description__icontains=search) | Q(reference_number__icontains=search)
        )

    total_income = transactions.filter(transaction_type='income', status='completed').aggregate(t=Sum('amount'))['t'] or 0
    total_expense = transactions.filter(transaction_type='expense', status='completed').aggregate(t=Sum('amount'))['t'] or 0

    context = {
        'transactions': transactions[:100],
        'accounts': FinancialAccount.objects.filter(active=True),
        'categories': TransactionCategory.objects.filter(active=True).order_by('category_type', 'name'),
        'type_filter': type_filter,
        'category_filter': category_filter,
        'account_filter': account_filter,
        'search': search,
        'total_income': total_income,
        'total_expense': total_expense,
    }
    return render(request, 'finance/transactions/list.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def transaction_create(request):
    _ensure_categories()
    if request.method == 'POST':
        member_id = request.POST.get('related_member')
        Transaction.objects.create(
            transaction_type=request.POST.get('transaction_type'),
            category_id=request.POST.get('category'),
            amount=request.POST.get('amount'),
            description=request.POST.get('description'),
            date=request.POST.get('date'),
            account_id=request.POST.get('account'),
            payment_method=request.POST.get('payment_method', 'cash'),
            status=request.POST.get('status', 'completed'),
            reference_number=request.POST.get('reference_number', ''),
            related_member_id=member_id if member_id else None,
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, 'Transacción registrada exitosamente.')
        return redirect('finance:transactions_list')

    context = {
        'accounts': FinancialAccount.objects.filter(active=True),
        'members': Member.objects.filter(status='active').order_by('last_name', 'first_name'),
        'income_categories': TransactionCategory.objects.filter(category_type='income', active=True).order_by('order', 'name'),
        'expense_categories': TransactionCategory.objects.filter(category_type='expense', active=True).order_by('order', 'name'),
        'payment_methods': Transaction.PAYMENT_METHOD_CHOICES,
        'action': 'Registrar',
        'today': timezone.now().date(),
    }
    return render(request, 'finance/transactions/form.html', context)


@login_required
@require_http_methods(['GET'])
def transaction_detail(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    return render(request, 'finance/transactions/detail.html', {'transaction': transaction})


@login_required
@require_http_methods(['GET', 'POST'])
def transaction_edit(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    if request.method == 'POST':
        member_id = request.POST.get('related_member')
        transaction.transaction_type = request.POST.get('transaction_type')
        transaction.category_id = request.POST.get('category')
        transaction.amount = request.POST.get('amount')
        transaction.description = request.POST.get('description')
        transaction.date = request.POST.get('date')
        transaction.account_id = request.POST.get('account')
        transaction.payment_method = request.POST.get('payment_method', 'cash')
        transaction.status = request.POST.get('status', 'completed')
        transaction.reference_number = request.POST.get('reference_number', '')
        transaction.related_member_id = member_id if member_id else None
        transaction.notes = request.POST.get('notes', '')
        transaction.save()
        messages.success(request, 'Transacción actualizada.')
        return redirect('finance:transactions_list')

    context = {
        'transaction': transaction,
        'accounts': FinancialAccount.objects.filter(active=True),
        'members': Member.objects.filter(status='active').order_by('last_name', 'first_name'),
        'income_categories': TransactionCategory.objects.filter(category_type='income', active=True).order_by('order', 'name'),
        'expense_categories': TransactionCategory.objects.filter(category_type='expense', active=True).order_by('order', 'name'),
        'payment_methods': Transaction.PAYMENT_METHOD_CHOICES,
        'action': 'Editar',
        'today': timezone.now().date(),
    }
    return render(request, 'finance/transactions/form.html', context)


@login_required
@require_http_methods(['POST'])
def transaction_delete(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    account = transaction.account
    transaction.delete()
    account.recalculate_balance()
    messages.success(request, 'Transacción eliminada.')
    return redirect('finance:transactions_list')


# ── Contribuciones ────────────────────────────────────────────────────────────

@login_required
@require_http_methods(['GET'])
def contributions_list(request):
    contributions = Contribution.objects.select_related('member', 'transaction', 'category').order_by('-date')

    category_filter = request.GET.get('category')
    if category_filter:
        contributions = contributions.filter(category_id=category_filter)

    search = request.GET.get('q', '').strip()
    if search:
        contributions = contributions.filter(
            Q(member__first_name__icontains=search) | Q(member__last_name__icontains=search)
        )

    total = contributions.aggregate(t=Sum('amount'))['t'] or 0

    context = {
        'contributions': contributions[:100],
        'income_categories': TransactionCategory.objects.filter(category_type='income', active=True).order_by('order', 'name'),
        'category_filter': category_filter,
        'search': search,
        'total': total,
    }
    return render(request, 'finance/contributions/list.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def contribution_create(request):
    _ensure_categories()
    if request.method == 'POST':
        member_id = request.POST.get('member')
        account_id = request.POST.get('account')
        amount = request.POST.get('amount')
        category_id = request.POST.get('category')
        date = request.POST.get('date')
        payment_method = request.POST.get('payment_method', 'cash')

        transaction = None
        if account_id:
            category = TransactionCategory.objects.get(id=category_id)
            member = Member.objects.get(id=member_id)
            transaction = Transaction.objects.create(
                transaction_type='income',
                category=category,
                amount=amount,
                description=f'{category.name} - {member.get_full_name()}',
                date=date,
                account_id=account_id,
                payment_method=payment_method,
                status='completed',
                related_member_id=member_id,
            )

        Contribution.objects.create(
            member_id=member_id,
            category_id=category_id,
            amount=amount,
            date=date,
            frequency=request.POST.get('frequency', 'one_time'),
            payment_method=payment_method,
            receipt_number=request.POST.get('receipt_number', ''),
            transaction=transaction,
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, 'Contribución registrada exitosamente.')
        return redirect('finance:contributions_list')

    context = {
        'members': Member.objects.filter(status='active').order_by('last_name', 'first_name'),
        'accounts': FinancialAccount.objects.filter(active=True),
        'income_categories': TransactionCategory.objects.filter(category_type='income', active=True).order_by('order', 'name'),
        'frequency_choices': Contribution.FREQUENCY_CHOICES,
        'payment_methods': Transaction.PAYMENT_METHOD_CHOICES,
        'today': timezone.now().date(),
    }
    return render(request, 'finance/contributions/form.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def contribution_edit(request, contribution_id):
    contribution = get_object_or_404(Contribution, id=contribution_id)
    if request.method == 'POST':
        contribution.category_id = request.POST.get('category')
        contribution.amount = request.POST.get('amount')
        contribution.date = request.POST.get('date')
        contribution.frequency = request.POST.get('frequency', 'one_time')
        contribution.payment_method = request.POST.get('payment_method', 'cash')
        contribution.receipt_number = request.POST.get('receipt_number', '')
        contribution.notes = request.POST.get('notes', '')
        contribution.save()
        messages.success(request, 'Contribución actualizada.')
        return redirect('finance:contributions_list')

    context = {
        'contribution': contribution,
        'members': Member.objects.filter(status='active').order_by('last_name', 'first_name'),
        'accounts': FinancialAccount.objects.filter(active=True),
        'income_categories': TransactionCategory.objects.filter(category_type='income', active=True).order_by('order', 'name'),
        'frequency_choices': Contribution.FREQUENCY_CHOICES,
        'payment_methods': Transaction.PAYMENT_METHOD_CHOICES,
        'today': timezone.now().date(),
    }
    return render(request, 'finance/contributions/form.html', context)


@login_required
@require_http_methods(['POST'])
def contribution_delete(request, contribution_id):
    contribution = get_object_or_404(Contribution, id=contribution_id)
    contribution.delete()
    messages.success(request, 'Contribución eliminada.')
    return redirect('finance:contributions_list')


# ── Presupuestos ──────────────────────────────────────────────────────────────

@login_required
@require_http_methods(['GET'])
def budgets_list(request):
    return render(request, 'finance/budgets/list.html', {'budgets': Budget.objects.all().order_by('-start_date')})


@login_required
@require_http_methods(['GET', 'POST'])
def budget_create(request):
    if request.method == 'POST':
        Budget.objects.create(
            name=request.POST.get('name'),
            period=request.POST.get('period'),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            total_income_budget=request.POST.get('total_income_budget') or 0,
            total_expense_budget=request.POST.get('total_expense_budget') or 0,
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, 'Presupuesto creado exitosamente.')
        return redirect('finance:budgets_list')
    return render(request, 'finance/budgets/form.html', {'action': 'Crear', 'today': timezone.now().date()})


@login_required
@require_http_methods(['GET'])
def budget_detail(request, budget_id):
    budget = get_object_or_404(Budget, id=budget_id)
    income_breakdown = (
        Transaction.objects.filter(transaction_type='income', status='completed', date__range=[budget.start_date, budget.end_date])
        .values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    expense_breakdown = (
        Transaction.objects.filter(transaction_type='expense', status='completed', date__range=[budget.start_date, budget.end_date])
        .values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    context = {
        'budget': budget,
        'actual_income': budget.get_actual_income(),
        'actual_expense': budget.get_actual_expense(),
        'income_variance': budget.get_income_variance(),
        'expense_variance': budget.get_expense_variance(),
        'income_breakdown': income_breakdown,
        'expense_breakdown': expense_breakdown,
    }
    return render(request, 'finance/budgets/detail.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def budget_edit(request, budget_id):
    budget = get_object_or_404(Budget, id=budget_id)
    if request.method == 'POST':
        budget.name = request.POST.get('name')
        budget.period = request.POST.get('period')
        budget.start_date = request.POST.get('start_date')
        budget.end_date = request.POST.get('end_date')
        budget.total_income_budget = request.POST.get('total_income_budget') or 0
        budget.total_expense_budget = request.POST.get('total_expense_budget') or 0
        budget.notes = request.POST.get('notes', '')
        budget.save()
        messages.success(request, 'Presupuesto actualizado.')
        return redirect('finance:budget_detail', budget_id=budget.id)
    return render(request, 'finance/budgets/form.html', {'budget': budget, 'action': 'Editar', 'today': timezone.now().date()})
