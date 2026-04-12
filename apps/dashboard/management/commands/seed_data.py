from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection

from apps.dashboard.models import SubscriptionPlan
from apps.organizations.models import Organization, Domain

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with initial data (tenants, admin user, subscription plans)'

    def handle(self, *args, **options):
        # Only create tenants if we're in the public schema
        schema_name = connection.schema_name
        
        if schema_name == 'public':
            self.stdout.write(self.style.WARNING('Running in public schema - setting up tenants...'))
            self._setup_tenants()
            self.stdout.write(self.style.SUCCESS('✅ Tenants configured\n'))
            return
        
        self.stdout.write(self.style.WARNING(f'Running in tenant schema: {schema_name}\n'))
        # Create admin user
        user, created = User.objects.get_or_create(
            email='admin@example.com',
            defaults={'is_staff': True, 'is_superuser': True, 'first_name': 'Admin'},
        )
        if created:
            user.set_password('admin123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Admin user created (admin@example.com / admin123)'))
        else:
            self.stdout.write('Admin user already exists')

        # Create subscription plans
        plans = [
            {
                'name': 'Free',
                'slug': 'free',
                'description': 'Get started with the basics',
                'price': 0,
                'interval': 'monthly',
                'features': ['Basic access', 'Community support', '1 project'],
            },
            {
                'name': 'Pro',
                'slug': 'pro',
                'description': 'For growing teams and businesses',
                'price': 9.99,
                'interval': 'monthly',
                'features': ['Everything in Free', 'Priority support', 'API access', '10 projects', 'Analytics'],
            },
            {
                'name': 'Enterprise',
                'slug': 'enterprise',
                'description': 'For large-scale operations',
                'price': 49.99,
                'interval': 'monthly',
                'features': [
                    'Everything in Pro',
                    'Dedicated support',
                    'Custom integrations',
                    'Unlimited projects',
                    'SLA guarantee',
                ],
            },
        ]

        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.get_or_create(
                slug=plan_data['slug'],
                defaults=plan_data,
            )
            status = 'created' if created else 'already exists'
            self.stdout.write(self.style.SUCCESS(f'Plan "{plan.name}" {status}'))

        self.stdout.write(self.style.SUCCESS('\nSeed data complete!'))

    def _setup_tenants(self):
        """Setup public and demo tenants with their domains"""
        
        # 1. Setup public tenant
        public_tenant, created = Organization.objects.get_or_create(
            schema_name='public',
            defaults={
                'name': 'Public',
                'subscription_status': 'active',
                'is_active': True
            }
        )
        
        if created:
            # Prevent auto schema creation since public already exists
            public_tenant.auto_create_schema = False
            public_tenant.save()
            self.stdout.write(self.style.SUCCESS('  ✅ Public tenant created'))
        else:
            self.stdout.write('  ℹ️  Public tenant already exists')
        
        # Create localhost domain for public tenant
        localhost_domain, created = Domain.objects.get_or_create(
            domain='localhost',
            defaults={
                'tenant': public_tenant,
                'is_primary': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('  ✅ localhost → public'))
        else:
            self.stdout.write('  ℹ️  localhost domain already exists')
        
        # 2. Setup demo tenant
        demo_tenant, created = Organization.objects.get_or_create(
            schema_name='demo',
            defaults={
                'name': 'Demo Church',
                'subscription_status': 'active',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('  ✅ Demo tenant created'))
        else:
            self.stdout.write('  ℹ️  Demo tenant already exists')
        
        # Create demo.localhost domain for demo tenant
        demo_domain, created = Domain.objects.get_or_create(
            domain='demo.localhost',
            defaults={
                'tenant': demo_tenant,
                'is_primary': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('  ✅ demo.localhost → demo'))
        else:
            self.stdout.write('  ℹ️  demo.localhost domain already exists')
