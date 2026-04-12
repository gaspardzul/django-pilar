from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class Organization(TenantMixin):
    name = models.CharField(max_length=100)
    created_on = models.DateField(auto_now_add=True)
    
    # Stripe subscription fields
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    subscription_status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('trialing', 'Trialing'),
            ('past_due', 'Past Due'),
            ('canceled', 'Canceled'),
            ('incomplete', 'Incomplete'),
        ],
        default='trialing'
    )
    
    # Organization settings
    is_active = models.BooleanField(default=True)
    max_users = models.IntegerField(default=10)
    
    auto_create_schema = True
    auto_drop_schema = False

    def __str__(self):
        return self.name


class Domain(DomainMixin):
    pass
