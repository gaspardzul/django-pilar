import uuid

from django.db import models
from django.utils import timezone

from apps.business.models import Member


class ServiceType(models.Model):
    """Tipo de actividad: Culto Dominical, Oración, Mensaje entre semana, Ensayo, etc."""

    WEEKDAY_CHOICES = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')
    default_weekdays = models.CharField(
        max_length=20, blank=True, verbose_name='Días habituales',
        help_text='Días de la semana separados por coma (0=Lun, 1=Mar, 2=Mié, 3=Jue, 4=Vie, 5=Sáb, 6=Dom)',
    )
    default_start_time = models.TimeField(null=True, blank=True, verbose_name='Hora de inicio')
    default_end_time = models.TimeField(null=True, blank=True, verbose_name='Hora de fin')
    color = models.CharField(
        max_length=7, default='#0B7FB3', verbose_name='Color de fondo',
        help_text='Color para el calendario (hex)',
    )
    text_color = models.CharField(
        max_length=7, default='#000000', verbose_name='Color de texto',
        help_text='Color del texto en el reporte impreso (hex)',
    )
    active = models.BooleanField(default=True, verbose_name='Activo')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='Orden')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'services_type'
        verbose_name = 'Tipo de Servicio'
        verbose_name_plural = 'Tipos de Servicio'
        ordering = ['order', 'name']

    def __str__(self):
        days = self.get_weekdays_display()
        return f'{self.name} ({days})' if days else self.name

    def get_weekdays_list(self):
        """Returns list of integers for selected weekdays."""
        if not self.default_weekdays:
            return []
        return [int(d.strip()) for d in self.default_weekdays.split(',') if d.strip().isdigit()]

    def get_weekdays_display(self):
        """Returns human-readable days string."""
        day_names = dict(self.WEEKDAY_CHOICES)
        return ', '.join(day_names.get(d, '') for d in self.get_weekdays_list())


class ServicePart(models.Model):
    """Parte/sección de un tipo de servicio: Alabanzas, Preside, Mensaje, Ujieres, etc."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name='parts', verbose_name='Tipo de servicio')
    name = models.CharField(max_length=100, verbose_name='Nombre de la parte')
    description = models.CharField(max_length=200, blank=True, verbose_name='Descripción')
    duration_minutes = models.PositiveIntegerField(default=30, verbose_name='Duración (min)')
    max_participants = models.PositiveIntegerField(
        default=1, verbose_name='Máx. participantes',
        help_text='Cuántas personas pueden asignarse a esta parte',
    )
    order = models.PositiveSmallIntegerField(default=0, verbose_name='Orden')
    active = models.BooleanField(default=True, verbose_name='Activa')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'services_part'
        verbose_name = 'Parte del Servicio'
        verbose_name_plural = 'Partes del Servicio'
        ordering = ['service_type', 'order']

    def __str__(self):
        return f'{self.name} ({self.service_type.name})'


class EligibleMember(models.Model):
    """Marca qué miembros pueden participar en qué partes del servicio."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='service_eligibilities', verbose_name='Miembro')
    service_part = models.ForeignKey(ServicePart, on_delete=models.CASCADE, related_name='eligible_members', verbose_name='Parte')
    notes = models.CharField(max_length=200, blank=True, verbose_name='Notas')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'services_eligible_member'
        verbose_name = 'Miembro Elegible'
        verbose_name_plural = 'Miembros Elegibles'
        unique_together = ['member', 'service_part']

    def __str__(self):
        return f'{self.member.get_full_name()} → {self.service_part.name}'


class ServiceSchedule(models.Model):
    """Un servicio programado en una fecha específica."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name='schedules', verbose_name='Tipo')
    date = models.DateField(verbose_name='Fecha')
    start_time = models.TimeField(null=True, blank=True, verbose_name='Hora inicio')
    end_time = models.TimeField(null=True, blank=True, verbose_name='Hora fin')
    title = models.CharField(max_length=200, blank=True, verbose_name='Título especial', help_text='Si es diferente al nombre del tipo')
    notes = models.TextField(blank=True, verbose_name='Notas')
    is_cancelled = models.BooleanField(default=False, verbose_name='Cancelado')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'services_schedule'
        verbose_name = 'Servicio Programado'
        verbose_name_plural = 'Servicios Programados'
        ordering = ['date', 'start_time']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['service_type', 'date']),
        ]

    def __str__(self):
        return f'{self.get_display_title()} — {self.date.strftime("%d/%m/%Y")}'

    def get_display_title(self):
        return self.title or self.service_type.name

    def get_assignments_by_part(self):
        """Retorna las asignaciones agrupadas por parte, en orden."""
        parts = self.service_type.parts.filter(active=True).order_by('order')
        result = []
        for part in parts:
            assignments = self.assignments.filter(service_part=part).select_related('member')
            result.append({
                'part': part,
                'assignments': assignments,
                'filled': assignments.count(),
                'max': part.max_participants,
            })
        return result


class ServiceAssignment(models.Model):
    """Asignación de un miembro a una parte de un servicio programado."""

    ROLE_CHOICES = [
        ('leader', 'Líder / Principal'),
        ('participant', 'Participante'),
        ('support', 'Apoyo'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule = models.ForeignKey(ServiceSchedule, on_delete=models.CASCADE, related_name='assignments', verbose_name='Servicio')
    service_part = models.ForeignKey(ServicePart, on_delete=models.CASCADE, related_name='assignments', verbose_name='Parte')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='service_assignments', verbose_name='Miembro')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='participant', verbose_name='Rol')
    confirmed = models.BooleanField(default=False, verbose_name='Confirmado')
    notes = models.CharField(max_length=200, blank=True, verbose_name='Notas')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'services_assignment'
        verbose_name = 'Asignación'
        verbose_name_plural = 'Asignaciones'
        unique_together = ['schedule', 'service_part', 'member']
        ordering = ['service_part__order', 'role']

    def __str__(self):
        return f'{self.member.get_full_name()} → {self.service_part.name} ({self.schedule.date})'


class MonthColor(models.Model):
    """Color personalizado para cada mes del reporte."""

    MONTH_CHOICES = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    month = models.IntegerField(choices=MONTH_CHOICES, unique=True, verbose_name='Mes')
    header_color = models.CharField(max_length=7, default='#1a3a5c', verbose_name='Color del encabezado')
    accent_color = models.CharField(max_length=7, default='#1a3a5c', verbose_name='Color de acento')

    class Meta:
        db_table = 'services_month_color'
        verbose_name = 'Color de Mes'
        verbose_name_plural = 'Colores de Mes'
        ordering = ['month']

    def __str__(self):
        return f'{self.get_month_display()} — {self.header_color}'
