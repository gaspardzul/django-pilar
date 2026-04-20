import uuid
from django.db import models
from django.utils import timezone


class Member(models.Model):
    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('visitor', 'Visitante'),
        ('transferred', 'Transferido'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    join_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    photo = models.ImageField(upload_to='members/', blank=True, null=True)
    notes = models.TextField(blank=True)
    
    # Baptism information
    is_baptized = models.BooleanField(default=False, verbose_name='Bautizado')
    baptism_date = models.DateField(null=True, blank=True, verbose_name='Fecha de bautismo')
    baptism_place = models.CharField(max_length=200, blank=True, verbose_name='Lugar de bautismo')
    baptized_by = models.CharField(max_length=200, blank=True, verbose_name='Bautizado por')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'business_member'
        verbose_name = 'Member'
        verbose_name_plural = 'Members'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['last_name', 'first_name']),
        ]
    
    def __str__(self):
        return self.get_full_name()
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_age(self):
        if not self.date_of_birth:
            return None
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


class Ministry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    leader = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_ministries'
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'business_ministry'
        verbose_name = 'Ministry'
        verbose_name_plural = 'Ministries'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_active_members(self):
        return self.member_ministries.filter(
            end_date__isnull=True,
            member__status='active'
        )
    
    def get_leaders(self):
        return self.member_ministries.filter(
            role__in=['leader', 'co_leader'],
            end_date__isnull=True
        )


class Family(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    family_name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    primary_contact = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_contact_for_families'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'business_family'
        verbose_name = 'Family'
        verbose_name_plural = 'Families'
        ordering = ['family_name']
    
    def __str__(self):
        return self.family_name
    
    def get_family_members(self):
        return self.family_members.filter(end_date__isnull=True)
    
    def get_family_structure(self):
        members = self.get_family_members()
        return {
            'parents': members.filter(relationship_type__in=['father', 'mother']),
            'children': members.filter(relationship_type='child'),
            'others': members.exclude(relationship_type__in=['father', 'mother', 'child'])
        }


class MemberMinistry(models.Model):
    ROLE_CHOICES = [
        ('leader', 'Líder'),
        ('co_leader', 'Co-Líder'),
        ('member', 'Miembro'),
        ('volunteer', 'Voluntario'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='ministry_memberships')
    ministry = models.ForeignKey(Ministry, on_delete=models.CASCADE, related_name='member_ministries')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'business_memberministry'
        verbose_name = 'Member Ministry'
        verbose_name_plural = 'Member Ministries'
        unique_together = ['member', 'ministry', 'start_date']
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.member.get_full_name()} - {self.ministry.name} ({self.get_role_display()})"
    
    def is_leader(self):
        return self.role in ['leader', 'co_leader']
    
    def is_active(self):
        return self.end_date is None


class FamilyMember(models.Model):
    RELATIONSHIP_CHOICES = [
        ('father', 'Padre'),
        ('mother', 'Madre'),
        ('child', 'Hijo/a'),
        ('spouse', 'Cónyuge'),
        ('sibling', 'Hermano/a'),
        ('grandparent', 'Abuelo/a'),
        ('grandchild', 'Nieto/a'),
        ('uncle_aunt', 'Tío/a'),
        ('nephew_niece', 'Sobrino/a'),
        ('cousin', 'Primo/a'),
        ('other', 'Otro'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='family_members')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='family_relationships')
    relationship_type = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    is_primary_contact = models.BooleanField(default=False)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'business_familymember'
        verbose_name = 'Family Member'
        verbose_name_plural = 'Family Members'
        unique_together = ['family', 'member', 'start_date']
        ordering = ['family', 'relationship_type']
    
    def __str__(self):
        return f"{self.member.get_full_name()} - {self.family.family_name} ({self.get_relationship_type_display()})"
    
    def is_active_member(self):
        return self.end_date is None
    
    def save(self, *args, **kwargs):
        # If this is set as primary contact, update the family
        if self.is_primary_contact:
            self.family.primary_contact = self.member
            self.family.save()
        super().save(*args, **kwargs)


# Events
class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=300)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    is_free_entry = models.BooleanField(default=True)
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_capacity = models.IntegerField(null=True, blank=True)
    event_type = models.CharField(
        max_length=50,
        choices=[
            ('service', 'Servicio'),
            ('conference', 'Conferencia'),
            ('retreat', 'Retiro'),
            ('workshop', 'Taller'),
            ('social', 'Social'),
            ('outreach', 'Alcance'),
            ('other', 'Otro'),
        ],
        default='service'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Borrador'),
            ('published', 'Publicado'),
            ('ongoing', 'En Curso'),
            ('completed', 'Completado'),
            ('cancelled', 'Cancelado'),
        ],
        default='draft'
    )
    organizer = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='organized_events'
    )
    notes = models.TextField(blank=True)
    requires_lodging = models.BooleanField(default=False, verbose_name='Requiere hospedaje')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'business_event'
        ordering = ['-start_date']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'

    def __str__(self):
        return self.name

    def get_status_display_es(self):
        status_map = {
            'draft': 'Borrador',
            'published': 'Publicado',
            'ongoing': 'En Curso',
            'completed': 'Completado',
            'cancelled': 'Cancelado',
        }
        return status_map.get(self.status, self.status)

    def get_total_workers(self):
        return EventWorker.objects.filter(
            work_group__event=self,
            status='confirmed'
        ).count()

    def get_work_groups(self):
        return self.work_groups.all()

    def is_upcoming(self):
        return self.start_date > timezone.now()

    def is_past(self):
        return self.end_date and self.end_date < timezone.now()


class EventWorkGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='work_groups'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    group_type = models.CharField(
        max_length=50,
        choices=[
            ('kitchen', 'Cocina'),
            ('reception', 'Recepción'),
            ('parking', 'Estacionamiento'),
            ('cleaning', 'Limpieza'),
            ('security', 'Seguridad'),
            ('sound', 'Sonido'),
            ('worship', 'Alabanza'),
            ('children', 'Niños'),
            ('youth', 'Jóvenes'),
            ('ushers', 'Ujieres'),
            ('prayer', 'Oración'),
            ('setup', 'Montaje'),
            ('teardown', 'Desmontaje'),
            ('other', 'Otro'),
        ],
        default='other'
    )
    coordinator = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coordinated_work_groups'
    )
    required_workers = models.IntegerField(default=1)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'business_eventworkgroup'
        ordering = ['name']
        verbose_name = 'Event Work Group'
        verbose_name_plural = 'Event Work Groups'

    def __str__(self):
        return f"{self.name} - {self.event.name}"

    def get_confirmed_workers(self):
        return self.workers.filter(status='confirmed')

    def get_workers_count(self):
        return self.workers.filter(status='confirmed').count()

    def is_fully_staffed(self):
        return self.get_workers_count() >= self.required_workers


class EventWorker(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work_group = models.ForeignKey(
        EventWorkGroup,
        on_delete=models.CASCADE,
        related_name='workers'
    )
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='event_assignments'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('invited', 'Invitado'),
            ('confirmed', 'Confirmado'),
            ('declined', 'Rechazado'),
            ('completed', 'Completado'),
        ],
        default='invited'
    )
    role = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'business_eventworker'
        unique_together = ['work_group', 'member']
        ordering = ['assigned_at']
        verbose_name = 'Event Worker'
        verbose_name_plural = 'Event Workers'

    def __str__(self):
        return f"{self.member.get_full_name()} - {self.work_group.name}"


# Event Budget and Finances
class EventBudget(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.OneToOneField(
        Event,
        on_delete=models.CASCADE,
        related_name='budget'
    )
    total_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    target_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Meta de recaudación")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'business_eventbudget'
        verbose_name = 'Event Budget'
        verbose_name_plural = 'Event Budgets'

    def __str__(self):
        return f"Presupuesto - {self.event.name}"

    def get_total_income(self):
        return self.incomes.aggregate(
            total=models.Sum('amount')
        )['total'] or 0

    def get_total_expenses(self):
        return self.expenses.aggregate(
            total=models.Sum('amount')
        )['total'] or 0

    def get_balance(self):
        return self.get_total_income() - self.get_total_expenses()

    def get_budget_usage_percentage(self):
        if self.total_budget > 0:
            return (self.get_total_expenses() / self.total_budget) * 100
        return 0

    def get_target_progress_percentage(self):
        """Porcentaje de progreso hacia la meta de recaudación"""
        if self.target_budget > 0:
            return (self.get_total_income() / self.target_budget) * 100
        return 0

    def has_reached_target(self):
        """Verifica si se alcanzó la meta de recaudación"""
        return self.get_total_income() >= self.target_budget if self.target_budget > 0 else False


class EventIncome(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    budget = models.ForeignKey(
        EventBudget,
        on_delete=models.CASCADE,
        related_name='incomes'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    source = models.CharField(
        max_length=50,
        choices=[
            ('donation', 'Donación'),
            ('offering', 'Ofrenda'),
            ('ticket_sales', 'Venta de Boletos'),
            ('sponsorship', 'Patrocinio'),
            ('fundraising', 'Recaudación'),
            ('other', 'Otro'),
        ],
        default='donation'
    )
    donor = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='event_donations'
    )
    description = models.CharField(max_length=300)
    date = models.DateField()
    receipt_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'business_eventincome'
        ordering = ['-date']
        verbose_name = 'Event Income'
        verbose_name_plural = 'Event Incomes'

    def __str__(self):
        return f"${self.amount} - {self.get_source_display()}"

    def get_donor_name(self):
        if self.donor:
            return self.donor.get_full_name()
        return "Anónimo"


class EventExpense(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    budget = models.ForeignKey(
        EventBudget,
        on_delete=models.CASCADE,
        related_name='expenses'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(
        max_length=50,
        choices=[
            ('venue', 'Lugar/Renta'),
            ('food', 'Alimentos'),
            ('equipment', 'Equipo'),
            ('materials', 'Materiales'),
            ('transportation', 'Transporte'),
            ('marketing', 'Marketing'),
            ('staff', 'Personal'),
            ('decoration', 'Decoración'),
            ('sound', 'Sonido/Audio'),
            ('other', 'Otro'),
        ],
        default='other'
    )
    description = models.CharField(max_length=300)
    vendor = models.CharField(max_length=200, blank=True)
    date = models.DateField()
    invoice_number = models.CharField(max_length=100, blank=True)
    paid_by = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='event_expenses_paid'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendiente'),
            ('paid', 'Pagado'),
            ('reimbursed', 'Reembolsado'),
        ],
        default='pending'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'business_eventexpense'
        ordering = ['-date']
        verbose_name = 'Event Expense'
        verbose_name_plural = 'Event Expenses'

    def __str__(self):
        return f"${self.amount} - {self.get_category_display()}"


# ── Hospedaje ─────────────────────────────────────────────────────────────────

class EventLodging(models.Model):
    """Configuración de hospedaje para un evento. Habilita el módulo y define la meta total."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='lodging')
    is_enabled = models.BooleanField(default=True, verbose_name='Hospedaje habilitado')
    total_needed = models.PositiveIntegerField(
        default=0,
        verbose_name='Total de personas a hospedar',
        help_text='Cuántas personas necesitan hospedaje para este evento',
    )
    notes = models.TextField(blank=True, verbose_name='Notas generales')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'business_event_lodging'
        verbose_name = 'Hospedaje de Evento'
        verbose_name_plural = 'Hospedajes de Evento'

    def __str__(self):
        return f'Hospedaje - {self.event.name}'

    def get_total_capacity(self):
        return self.hosts.filter(active=True).aggregate(
            total=models.Sum('capacity')
        )['total'] or 0

    def get_total_assigned(self):
        return self.hosts.filter(active=True).aggregate(
            total=models.Sum('assigned_count')
        )['total'] or 0

    def get_available_spots(self):
        return self.get_total_capacity() - self.get_total_assigned()

    def is_covered(self):
        """¿La capacidad ofrecida cubre la meta del evento?"""
        return self.get_total_capacity() >= self.total_needed if self.total_needed > 0 else False

    def coverage_percentage(self):
        if self.total_needed > 0:
            return min(round((self.get_total_capacity() / self.total_needed) * 100), 100)
        return 0


class LodgingHost(models.Model):
    """Hermano que ofrece su casa/espacio para hospedar durante el evento."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lodging = models.ForeignKey(EventLodging, on_delete=models.CASCADE, related_name='hosts')
    host = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lodging_offers',
        verbose_name='Anfitrión',
    )
    host_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Nombre del anfitrión',
        help_text='Si no es miembro registrado, escribe el nombre aquí',
    )
    address = models.TextField(verbose_name='Dirección / Ubicación')
    latitude = models.CharField(max_length=20, blank=True, verbose_name='Latitud')
    longitude = models.CharField(max_length=20, blank=True, verbose_name='Longitud')
    capacity = models.PositiveIntegerField(verbose_name='Capacidad (personas)')
    assigned_count = models.PositiveIntegerField(default=0, verbose_name='Personas asignadas')
    active = models.BooleanField(default=True, verbose_name='Disponible')
    notes = models.TextField(
        blank=True,
        verbose_name='Notas',
        help_text='Ej: tiene 2 hamacas, requieren llevar colchas, hay 1 cama matrimonial, etc.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'business_lodging_host'
        verbose_name = 'Anfitrión'
        verbose_name_plural = 'Anfitriones'
        ordering = ['host_name', 'host__last_name']

    def __str__(self):
        name = self.get_display_name()
        return f'{name} ({self.assigned_count}/{self.capacity})'

    def get_display_name(self):
        if self.host:
            return self.host.get_full_name()
        return self.host_name or 'Sin nombre'

    def available_spots(self):
        return max(self.capacity - self.assigned_count, 0)

    def is_full(self):
        return self.assigned_count >= self.capacity


class LodgingGuest(models.Model):
    """Grupo de personas asignadas a un anfitrión."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    host = models.ForeignKey(LodgingHost, on_delete=models.CASCADE, related_name='guests')
    representative = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lodging_as_guest',
        verbose_name='Representante del grupo',
    )
    representative_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Nombre del representante',
        help_text='Si no es miembro registrado',
    )
    adults = models.PositiveIntegerField(default=1, verbose_name='Adultos')
    children = models.PositiveIntegerField(default=0, verbose_name='Niños')
    notes = models.TextField(blank=True, verbose_name='Notas')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'business_lodging_guest'
        verbose_name = 'Grupo Huésped'
        verbose_name_plural = 'Grupos Huéspedes'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.get_display_name()} ({self.total_people()} personas)'

    def get_display_name(self):
        if self.representative:
            return self.representative.get_full_name()
        return self.representative_name or 'Sin nombre'

    def total_people(self):
        return self.adults + self.children

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Recalculate assigned_count on the host
        self.host.assigned_count = sum(g.total_people() for g in self.host.guests.all())
        self.host.save(update_fields=['assigned_count'])
