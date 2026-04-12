from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from django_tenants.utils import schema_context
import re

from apps.organizations.models import Organization, Domain
from .models import OrganizationMembership


def generate_schema_name(org_name):
    """Generate a valid schema name from organization name."""
    # Remove invalid characters and convert to lowercase
    schema_name = re.sub(r'[^a-z0-9_]', '', org_name.lower())
    # Replace spaces with underscores
    schema_name = schema_name.replace(' ', '_')
    # Ensure it starts with a letter
    if not schema_name or not schema_name[0].isalpha():
        schema_name = 'org_' + schema_name
    # Truncate to max 63 chars (PostgreSQL limit)
    schema_name = schema_name[:63]
    
    # Check if schema already exists, append number if needed
    base_schema = schema_name
    counter = 1
    while Organization.objects.filter(schema_name=schema_name).exists():
        schema_name = f"{base_schema}{counter}"[:63]
        counter += 1
    
    return schema_name


@receiver(user_signed_up)
def create_organization_on_signup(sender, request, user, **kwargs):
    """
    Automatically create an organization and assign the user as owner
    when they sign up.
    """
    # Skip if user already has an organization
    if OrganizationMembership.objects.filter(user=user, role='owner').exists():
        return
    
    # Get organization name from session (set by CustomSignupForm)
    org_name = request.session.get('organization_name')
    
    # Fallback to email-based name if not in session
    if not org_name:
        username = user.email.split('@')[0]
        org_name = f"{username.title()}'s Organization"
    
    # Generate schema name from organization name
    schema_name = generate_schema_name(org_name)
    
    # Create organization (tenant)
    organization = Organization.objects.create(
        schema_name=schema_name,
        name=org_name,
        subscription_status='trialing',
        is_active=True,
        max_users=10,
    )
    
    # Create domain for the organization
    # In production, you might want to use actual subdomains
    domain_name = f"{schema_name}.localhost"
    Domain.objects.create(
        domain=domain_name,
        tenant=organization,
        is_primary=True
    )
    
    # Create membership record
    OrganizationMembership.objects.create(
        user=user,
        organization_schema=schema_name,
        role='owner',
        is_active=True
    )
    
    # Create user in the tenant schema
    with schema_context(schema_name):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Create the same user in the tenant schema
        if not User.objects.filter(email=user.email).exists():
            User.objects.create_user(
                email=user.email,
                password=None,  # Password is already set in public schema
                first_name=user.first_name,
                last_name=user.last_name,
            )
    
    # Clean up session
    if 'organization_name' in request.session:
        del request.session['organization_name']
    
    print(f"✓ Organization created: {org_name} (schema: {schema_name})")
    print(f"  Domain: {domain_name}")
    print(f"  Owner: {user.email}")
