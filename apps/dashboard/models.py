import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    interval = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
        ],
        default='monthly'
    )
    features = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'

    def __str__(self):
        return f"{self.name} ({self.get_interval_display()})"

class UserSettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='settings'
    )
    # Notification preferences
    notify_comments = models.BooleanField(default=False)
    notify_updates = models.BooleanField(default=False)
    notify_marketing = models.BooleanField(default=False)

    # API settings
    api_key = models.CharField(max_length=64, blank=True, default='')
    api_key_created_at = models.DateTimeField(null=True, blank=True)

    # Subscription settings
    subscription_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscribers'
    )
    subscription_status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('cancelled', 'Cancelled'),
            ('trial', 'Trial'),
        ],
        default='inactive'
    )
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    trial_end_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Settings'
        verbose_name_plural = 'User Settings'

    def __str__(self):
        return f"Settings for {self.user.email}"

    @property
    def is_subscription_active(self):
        if self.subscription_status != 'active':
            return False
        if self.subscription_end_date and self.subscription_end_date < timezone.now():
            return False
        return True

    @property
    def is_trial_active(self):
        if self.subscription_status != 'trial':
            return False
        if self.trial_end_date and self.trial_end_date < timezone.now():
            return False
        return True


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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
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
