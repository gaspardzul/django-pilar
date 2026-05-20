import calendar
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.business.models import Member

from .models import EligibleMember, ServiceAssignment, ServicePart, ServiceSchedule, ServiceType


# ── Calendario ────────────────────────────────────────────────────────────────

@login_required
@require_http_methods(['GET'])
def calendar_view(request):
    today = timezone.now().date()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    # Build calendar weeks
    cal = calendar.Calendar(firstweekday=0)  # Monday first
    month_days = cal.monthdayscalendar(year, month)

    # Get all schedules for this month
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    schedules = ServiceSchedule.objects.filter(
        date__gte=first_day, date__lte=last_day
    ).select_related('service_type').prefetch_related('assignments__member', 'assignments__service_part')

    # Also get Events from the events module
    from apps.business.models import Event as BusinessEvent
    events = BusinessEvent.objects.filter(
        start_date__date__gte=first_day, start_date__date__lte=last_day
    ).order_by('start_date')

    # Index schedules by day
    schedules_by_day = {}
    for s in schedules:
        schedules_by_day.setdefault(s.date.day, []).append(s)

    # Index events by day
    events_by_day = {}
    for e in events:
        events_by_day.setdefault(e.start_date.day, []).append(e)

    # Build calendar weeks with schedules embedded
    weeks_data = []
    for week in month_days:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append({'day': 0, 'schedules': [], 'events': []})
            else:
                week_data.append({
                    'day': day,
                    'schedules': schedules_by_day.get(day, []),
                    'events': events_by_day.get(day, []),
                })
        weeks_data.append(week_data)

    # Navigation
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    month_name = [
        '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ][month]

    context = {
        'year': year,
        'month': month,
        'month_name': month_name,
        'weeks_data': weeks_data,
        'today': today,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'service_types': ServiceType.objects.filter(active=True),
    }
    return render(request, 'services/calendar.html', context)


# ── Tipos de Servicio ─────────────────────────────────────────────────────────

@login_required
@require_http_methods(['GET'])
def service_types_list(request):
    types = ServiceType.objects.prefetch_related('parts').order_by('order', 'name')
    return render(request, 'services/types/list.html', {'service_types': types})


@login_required
@require_http_methods(['GET', 'POST'])
def service_type_create(request):
    if request.method == 'POST':
        weekdays = ','.join(request.POST.getlist('default_weekdays'))
        ServiceType.objects.create(
            name=request.POST.get('name'),
            description=request.POST.get('description', ''),
            default_weekdays=weekdays,
            default_start_time=request.POST.get('default_start_time') or None,
            default_end_time=request.POST.get('default_end_time') or None,
            color=request.POST.get('color', '#0B7FB3'),
            text_color=request.POST.get('text_color', '#000000'),
        )
        messages.success(request, 'Tipo de servicio creado.')
        return redirect('services:types_list')
    return render(request, 'services/types/form.html', {'action': 'Crear'})


@login_required
@require_http_methods(['GET', 'POST'])
def service_type_edit(request, type_id):
    stype = get_object_or_404(ServiceType, id=type_id)
    if request.method == 'POST':
        weekdays = ','.join(request.POST.getlist('default_weekdays'))
        stype.name = request.POST.get('name')
        stype.description = request.POST.get('description', '')
        stype.default_weekdays = weekdays
        stype.default_start_time = request.POST.get('default_start_time') or None
        stype.default_end_time = request.POST.get('default_end_time') or None
        stype.color = request.POST.get('color', '#0B7FB3')
        stype.text_color = request.POST.get('text_color', '#000000')
        stype.active = request.POST.get('active') == 'on'
        stype.save()
        messages.success(request, f'Tipo "{stype.name}" actualizado.')
        return redirect('services:types_list')
    return render(request, 'services/types/form.html', {'service_type': stype, 'action': 'Editar'})


# ── Partes del Servicio ───────────────────────────────────────────────────────

@login_required
@require_http_methods(['GET'])
def service_type_parts(request, type_id):
    stype = get_object_or_404(ServiceType, id=type_id)
    parts = stype.parts.order_by('order')
    return render(request, 'services/types/parts.html', {'service_type': stype, 'parts': parts})


@login_required
@require_http_methods(['GET', 'POST'])
def service_part_create(request, type_id):
    stype = get_object_or_404(ServiceType, id=type_id)
    if request.method == 'POST':
        ServicePart.objects.create(
            service_type=stype,
            name=request.POST.get('name'),
            description=request.POST.get('description', ''),
            duration_minutes=request.POST.get('duration_minutes', 30),
            max_participants=request.POST.get('max_participants', 1),
            order=request.POST.get('order', 0),
        )
        messages.success(request, 'Parte creada exitosamente.')
        return redirect('services:type_parts', type_id=stype.id)
    return render(request, 'services/types/part_form.html', {'service_type': stype, 'action': 'Crear'})


@login_required
@require_http_methods(['GET', 'POST'])
def service_part_edit(request, type_id, part_id):
    stype = get_object_or_404(ServiceType, id=type_id)
    part = get_object_or_404(ServicePart, id=part_id, service_type=stype)
    if request.method == 'POST':
        part.name = request.POST.get('name')
        part.description = request.POST.get('description', '')
        part.duration_minutes = request.POST.get('duration_minutes', 30)
        part.max_participants = request.POST.get('max_participants', 1)
        part.order = request.POST.get('order', 0)
        part.active = request.POST.get('active') == 'on'
        part.save()
        messages.success(request, f'Parte "{part.name}" actualizada.')
        return redirect('services:type_parts', type_id=stype.id)
    return render(request, 'services/types/part_form.html', {'service_type': stype, 'part': part, 'action': 'Editar'})


# ── Miembros Elegibles ────────────────────────────────────────────────────────

@login_required
@require_http_methods(['GET'])
def part_eligible_members(request, type_id, part_id):
    stype = get_object_or_404(ServiceType, id=type_id)
    part = get_object_or_404(ServicePart, id=part_id, service_type=stype)
    members = Member.objects.filter(status='active').order_by('last_name', 'first_name')
    eligible_ids = set(part.eligible_members.values_list('member_id', flat=True))
    context = {
        'service_type': stype,
        'part': part,
        'members': members,
        'eligible_ids': eligible_ids,
    }
    return render(request, 'services/types/eligible.html', context)


@login_required
@require_http_methods(['POST'])
def part_toggle_eligible(request, type_id, part_id):
    part = get_object_or_404(ServicePart, id=part_id, service_type_id=type_id)
    member_id = request.POST.get('member_id')
    member = get_object_or_404(Member, id=member_id)

    existing = EligibleMember.objects.filter(member=member, service_part=part)
    if existing.exists():
        existing.delete()
        messages.success(request, f'{member.get_full_name()} removido de "{part.name}".')
    else:
        EligibleMember.objects.create(member=member, service_part=part)
        messages.success(request, f'{member.get_full_name()} agregado a "{part.name}".')

    return redirect('services:part_eligible', type_id=type_id, part_id=part_id)


# ── Servicios Programados ─────────────────────────────────────────────────────

@login_required
@require_http_methods(['GET', 'POST'])
def schedule_create(request):
    if request.method == 'POST':
        stype_id = request.POST.get('service_type')
        stype = get_object_or_404(ServiceType, id=stype_id)
        schedule = ServiceSchedule.objects.create(
            service_type=stype,
            date=request.POST.get('date'),
            start_time=request.POST.get('start_time') or stype.default_start_time,
            end_time=request.POST.get('end_time') or stype.default_end_time,
            title=request.POST.get('title', ''),
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, f'Servicio programado para {schedule.date}.')
        return redirect('services:schedule_detail', schedule_id=schedule.id)

    context = {
        'service_types': ServiceType.objects.filter(active=True),
        'today': request.GET.get('date', str(timezone.now().date())),
    }
    return render(request, 'services/schedule/form.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def schedule_edit(request, schedule_id):
    schedule = get_object_or_404(ServiceSchedule, id=schedule_id)
    if request.method == 'POST':
        schedule.title = request.POST.get('title', '')
        schedule.start_time = request.POST.get('start_time') or None
        schedule.end_time = request.POST.get('end_time') or None
        schedule.notes = request.POST.get('notes', '')
        schedule.is_cancelled = request.POST.get('is_cancelled') == 'on'
        schedule.save()
        messages.success(request, 'Servicio actualizado.')
        return redirect('services:schedule_detail', schedule_id=schedule.id)
    return render(request, 'services/schedule/edit.html', {'schedule': schedule})


@login_required
@require_http_methods(['GET'])
def schedule_detail(request, schedule_id):
    schedule = get_object_or_404(ServiceSchedule, id=schedule_id)
    parts_data = schedule.get_assignments_by_part()

    # Get eligible members for each part
    for item in parts_data:
        assigned_ids = set(item['assignments'].values_list('member_id', flat=True))
        item['available_members'] = Member.objects.filter(
            status='active', is_service_eligible=True
        ).exclude(id__in=assigned_ids).order_by('last_name', 'first_name')

    context = {
        'schedule': schedule,
        'parts_data': parts_data,
    }
    return render(request, 'services/schedule/detail.html', context)


@login_required
@require_http_methods(['POST'])
def schedule_assign(request, schedule_id):
    schedule = get_object_or_404(ServiceSchedule, id=schedule_id)
    part_id = request.POST.get('service_part')
    member_id = request.POST.get('member')
    role = request.POST.get('role', 'participant')

    ServiceAssignment.objects.get_or_create(
        schedule=schedule,
        service_part_id=part_id,
        member_id=member_id,
        defaults={'role': role, 'notes': request.POST.get('notes', '')},
    )
    messages.success(request, 'Participante asignado.')
    return redirect('services:schedule_detail', schedule_id=schedule.id)


@login_required
@require_http_methods(['POST'])
def schedule_remove_assignment(request, schedule_id, assignment_id):
    assignment = get_object_or_404(ServiceAssignment, id=assignment_id, schedule_id=schedule_id)
    assignment.delete()
    messages.success(request, 'Asignación eliminada.')
    return redirect('services:schedule_detail', schedule_id=schedule_id)


@login_required
@require_http_methods(['POST'])
def schedule_delete(request, schedule_id):
    schedule = get_object_or_404(ServiceSchedule, id=schedule_id)
    year = schedule.date.year
    month = schedule.date.month
    schedule.delete()
    messages.success(request, 'Servicio eliminado del calendario.')
    return redirect(f'/services/?year={year}&month={month}')


# ── Generar Mes ───────────────────────────────────────────────────────────────

@login_required
@require_http_methods(['GET', 'POST'])
def generate_month(request):
    """Genera automáticamente los servicios de un mes basado en los tipos activos y sus días."""
    if request.method == 'POST':
        year = int(request.POST.get('year'))
        month = int(request.POST.get('month'))
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])

        types = ServiceType.objects.filter(active=True).exclude(default_weekdays='')
        created = 0

        current = first_day
        while current <= last_day:
            for stype in types:
                if current.weekday() in stype.get_weekdays_list():
                    _, was_created = ServiceSchedule.objects.get_or_create(
                        service_type=stype,
                        date=current,
                        defaults={
                            'start_time': stype.default_start_time,
                            'end_time': stype.default_end_time,
                        },
                    )
                    if was_created:
                        created += 1
            current += timedelta(days=1)

        messages.success(request, f'{created} servicios generados para {month}/{year}.')
        return redirect('services:calendar')

    today = timezone.now().date()
    context = {
        'current_year': today.year,
        'current_month': today.month,
    }
    return render(request, 'services/generate.html', context)


# ── Reiniciar Mes ─────────────────────────────────────────────────────────────

@login_required
@require_http_methods(['POST'])
def reset_month(request):
    """Elimina todos los servicios programados de un mes."""
    year = int(request.POST.get('year'))
    month = int(request.POST.get('month'))

    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])

    deleted_count = ServiceSchedule.objects.filter(date__gte=first_day, date__lte=last_day).delete()[0]

    month_names = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                   'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    messages.success(request, f'{month_names[month]} {year} reiniciado: {deleted_count} elemento(s) eliminado(s).')
    return redirect(f'/services/?year={year}&month={month}')


# ── Clonar Mes ────────────────────────────────────────────────────────────────
@login_required
@require_http_methods(['GET', 'POST'])
def clone_month(request):
    """Clona servicios y asignaciones de un mes origen a un mes destino."""
    if request.method == 'POST':
        src_year = int(request.POST.get('src_year'))
        src_month = int(request.POST.get('src_month'))
        dst_year = int(request.POST.get('dst_year'))
        dst_month = int(request.POST.get('dst_month'))

        src_first = date(src_year, src_month, 1)
        src_last = date(src_year, src_month, calendar.monthrange(src_year, src_month)[1])

        src_schedules = ServiceSchedule.objects.filter(
            date__gte=src_first, date__lte=src_last, is_cancelled=False
        ).prefetch_related('assignments')

        if not src_schedules.exists():
            messages.error(request, f'No hay servicios en {src_month}/{src_year} para clonar.')
            return redirect('services:clone_month')

        created_schedules = 0
        created_assignments = 0

        for src in src_schedules:
            # Calculate equivalent date in destination month
            # Same weekday, same week number within the month
            src_day = src.date.day
            dst_last_day = calendar.monthrange(dst_year, dst_month)[1]
            dst_day = min(src_day, dst_last_day)

            # Try to find the same weekday in the same week position
            src_weekday = src.date.weekday()
            src_week_in_month = (src.date.day - 1) // 7  # 0-based week

            # Find the nth occurrence of that weekday in dst month
            dst_first = date(dst_year, dst_month, 1)
            first_weekday = dst_first.weekday()
            # Days until first occurrence of target weekday
            days_to_first = (src_weekday - first_weekday) % 7
            target_day = 1 + days_to_first + (src_week_in_month * 7)

            if target_day > dst_last_day:
                # If it exceeds the month, use last occurrence
                target_day -= 7

            if target_day < 1:
                target_day = 1

            target_date = date(dst_year, dst_month, target_day)

            # Check if already exists
            existing = ServiceSchedule.objects.filter(
                service_type=src.service_type, date=target_date
            ).exists()

            if not existing:
                new_schedule = ServiceSchedule.objects.create(
                    service_type=src.service_type,
                    date=target_date,
                    start_time=src.start_time,
                    end_time=src.end_time,
                    title=src.title,
                    notes='',
                )
                created_schedules += 1

                # Clone assignments only if requested
                if request.POST.get('clone_assignments') == 'on':
                    for assignment in src.assignments.all():
                        ServiceAssignment.objects.create(
                            schedule=new_schedule,
                            service_part=assignment.service_part,
                            member=assignment.member,
                            role=assignment.role,
                            notes=assignment.notes,
                        )
                        created_assignments += 1

        messages.success(
            request,
            f'Clonado exitoso: {created_schedules} servicios y {created_assignments} asignaciones creados para {dst_month}/{dst_year}.'
        )
        return redirect('services:calendar')

    today = timezone.now().date()
    context = {
        'current_year': today.year,
        'current_month': today.month,
    }
    return render(request, 'services/clone.html', context)


# ── Reporte Mensual Imprimible ────────────────────────────────────────────────
@login_required
@require_http_methods(['GET'])
def monthly_report(request):
    today = timezone.now().date()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)

    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])

    schedules = ServiceSchedule.objects.filter(
        date__gte=first_day, date__lte=last_day, is_cancelled=False
    ).select_related('service_type').prefetch_related(
        'assignments__member', 'assignments__service_part'
    ).order_by('date', 'start_time')

    # Index by day
    schedules_by_day = {}
    for s in schedules:
        schedules_by_day.setdefault(s.date.day, []).append(s)

    # Build weeks with data
    weeks_data = []
    for week in month_days:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append({'day': 0, 'schedules': []})
            else:
                week_data.append({'day': day, 'schedules': schedules_by_day.get(day, [])})
        weeks_data.append(week_data)

    month_name = [
        '', 'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO',
        'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE'
    ][month]

    # Get month color
    from .models import MonthColor
    try:
        month_color = MonthColor.objects.get(month=month)
        header_color = month_color.header_color
        accent_color = month_color.accent_color
    except MonthColor.DoesNotExist:
        header_color = '#1a3a5c'
        accent_color = '#1a3a5c'

    context = {
        'year': year,
        'month': month,
        'month_name': month_name,
        'weeks_data': weeks_data,
        'header_color': header_color,
        'accent_color': accent_color,
    }
    return render(request, 'services/report.html', context)


# ── Colores de Mes ────────────────────────────────────────────────────────────

@login_required
@require_http_methods(['GET', 'POST'])
def month_colors(request):
    from .models import MonthColor

    MONTHS = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
    ]

    if request.method == 'POST':
        for num, name in MONTHS:
            header = request.POST.get(f'header_{num}', '#1a3a5c')
            accent = request.POST.get(f'accent_{num}', '#1a3a5c')
            MonthColor.objects.update_or_create(
                month=num,
                defaults={'header_color': header, 'accent_color': accent},
            )
        messages.success(request, 'Colores de mes actualizados.')
        return redirect('services:month_colors')

    # Load existing colors
    existing = {mc.month: mc for mc in MonthColor.objects.all()}
    months_data = []
    for num, name in MONTHS:
        mc = existing.get(num)
        months_data.append({
            'num': num,
            'name': name,
            'header_color': mc.header_color if mc else '#1a3a5c',
            'accent_color': mc.accent_color if mc else '#1a3a5c',
        })

    return render(request, 'services/month_colors.html', {'months_data': months_data})
