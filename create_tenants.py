import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.organizations.models import Organization, Domain

print("Creando tenants...")

# Create public tenant
public_tenant, created = Organization.objects.get_or_create(
    schema_name='public',
    defaults={
        'name': 'Public',
        'is_active': True,
    }
)

if created:
    print("✓ Tenant público creado")
    # Create domain for public tenant
    Domain.objects.create(
        domain='localhost',
        tenant=public_tenant,
        is_primary=True
    )
    print("  - Dominio: localhost")
else:
    print("  Tenant público ya existe")

# Create demo tenant
demo_tenant, created = Organization.objects.get_or_create(
    schema_name='demo',
    defaults={
        'name': 'Demo Church',
        'is_active': True,
        'subscription_status': 'trialing',
        'max_users': 50,
    }
)

if created:
    print("✓ Tenant demo creado")
    # Create domain for demo tenant
    Domain.objects.create(
        domain='demo.localhost',
        tenant=demo_tenant,
        is_primary=True
    )
    print("  - Dominio: demo.localhost")
    print("  - Schema: demo")
else:
    print("  Tenant demo ya existe")

print("\n=== Tenants disponibles ===")
for org in Organization.objects.all():
    domains = Domain.objects.filter(tenant=org)
    print(f"\n{org.name} (schema: {org.schema_name})")
    for domain in domains:
        print(f"  → {domain.domain} {'(primary)' if domain.is_primary else ''}")
