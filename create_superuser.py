import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context

User = get_user_model()

# Create superuser in public schema
with schema_context('public'):
    if not User.objects.filter(email='admin@example.com').exists():
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )
        print("✓ Superusuario creado en schema público")
        print("  Email: admin@example.com")
        print("  Password: admin123")
    else:
        print("  Superusuario ya existe en schema público")

# Create demo user in demo schema
with schema_context('demo'):
    if not User.objects.filter(email='demo@example.com').exists():
        user = User.objects.create_user(
            email='demo@example.com',
            password='demo123'
        )
        print("\n✓ Usuario demo creado en schema demo")
        print("  Email: demo@example.com")
        print("  Password: demo123")
    else:
        print("\n  Usuario demo ya existe en schema demo")
