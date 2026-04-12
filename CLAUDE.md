# Pilar Software

## Overview
Sistema multi-tenant de gestión de iglesias con autenticación por email y frontend moderno. Construido con Django 6.0 y Python 3.12.

**Multi-Tenancy:** Usa `django-tenants` con esquemas de PostgreSQL - cada organización/iglesia tiene su propio esquema de base de datos aislado.

## Tech Stack
- **Backend:** Django 6.0, Python 3.12
- **Auth:** django-allauth (email-only, no username)
- **Multi-Tenancy:** django-tenants (shared database, separate schemas)
- **Payments:** Stripe (Payment Methods API)
- **Frontend:** Tailwind CSS (CDN) + Alpine.js + HTMX
- **Database:** PostgreSQL (required for multi-tenancy)
- **Static Files:** WhiteNoise
- **Server:** Gunicorn
- **Background Tasks:** Django 6.0 native `@task()` decorator
- **Linting:** Ruff

## Project Structure
```
core/           → Settings, URLs, WSGI/ASGI
  urls.py       → Public tenant URLs (landing, signup)
  urls_tenants.py → Tenant-specific URLs (dashboard, app features)
apps/
  accounts/     → CustomUser model (email-only), admin (SHARED)
  organizations/→ Organization (tenant) model, domains (SHARED)
  dashboard/    → Dashboard, profile, settings (TENANT)
  landing/      → Public pages (home, pricing, features) (TENANT)
  subscriptions/→ Stripe integration, webhooks (TENANT)
templates/      → All HTML templates (Tailwind + Alpine.js)
static/         → CSS, JS, images
```

## Key Conventions

### Multi-Tenancy
- **Architecture:** Shared database, separate schemas per organization
- **Tenant Model:** `apps.organizations.Organization` with `schema_name` field
- **Domain Routing:** Subdomains route to tenants (e.g., `demo.localhost` → demo schema)
- **Shared Apps:** `accounts`, `organizations` (available in public schema)
- **Tenant Apps:** `dashboard`, `landing`, `subscriptions` (isolated per tenant)
- **Schema Context:** Use `from django_tenants.utils import schema_context` to switch schemas

### User Model
- Custom user model at `apps.accounts.CustomUser` — email-only, no username
- Users are stored in the **public schema** (shared across all tenants)
- Use `settings.AUTH_USER_MODEL` for ForeignKey/OneToOneField references
- Use `get_user_model()` for queries

### Views
- Function-based views with `@login_required` and `@require_http_methods` decorators
- App-specific URL namespaces: `landing:home`, `dashboard:home`, `dashboard:profile`, etc.

### Django 6.0 Features
- **CSP:** Configured via `SECURE_CSP` in settings, nonces available as `{{ csp_nonce }}` in templates
- **Background Tasks:** Use `@task` decorator, enqueue with `.enqueue()` — see `apps/dashboard/tasks.py`
- **Template Partials:** Use `{% partialdef name inline %}` and `{% partial name %}` for reusable components

### Templates
- Design system: monochromatic (black/white/gray), Space Grotesk font, uppercase tracking
- All external scripts/styles use `nonce="{{ csp_nonce }}"` for CSP
- Two base templates: `templates/base.html` (public) and `templates/dashboard/base.html` (authenticated)

## Commands
```bash
make install    # Create venv and install dependencies
make run        # Start development server
make migrate    # Run makemigrations + migrate
make test       # Run tests
make seed       # Populate demo data (admin + plans)
make lint       # Lint with ruff
make format     # Format with ruff
make superuser  # Create admin user

# Multi-tenancy commands
python manage.py migrate_schemas --shared  # Migrate public schema only
python manage.py migrate_schemas           # Migrate all tenant schemas
python create_tenants.py                   # Create public + demo tenants
python create_superuser.py                 # Create admin users
python reset_db.py                         # Reset PostgreSQL database
```

## Environment
Copy `.env.example` to `.env`. Key variables:
- `SECRET_KEY` — Django secret key
- `DATABASE_URL` — PostgreSQL connection (REQUIRED for multi-tenancy)
  - Example: `postgres://user:password@localhost:5432/dbname`
- `STRIPE_*` — Stripe API keys
- `EMAIL_*` — SMTP configuration

## Multi-Tenancy Setup

### Initial Setup
1. **Create PostgreSQL database:**
   ```bash
   createdb pilardb
   ```

2. **Configure DATABASE_URL in `.env`:**
   ```
   DATABASE_URL=postgres://admin:admin@localhost:5432/pilardb
   ```

3. **Run migrations:**
   ```bash
   python manage.py migrate_schemas --shared
   ```

4. **Create tenants:**
   ```bash
   python create_tenants.py
   ```

5. **Create users:**
   ```bash
   python create_superuser.py
   ```

### Accessing Tenants
- **Public tenant:** `http://localhost:8000` (landing pages, signup)
- **Demo tenant:** `http://demo.localhost:8000` (demo organization)
- **Admin:** `http://localhost:8000/admin` (public schema admin)

### Creating New Tenants
```python
from apps.organizations.models import Organization, Domain

# Create organization
org = Organization.objects.create(
    schema_name='myorg',
    name='My Organization',
    subscription_status='trialing'
)

# Create domain
Domain.objects.create(
    domain='myorg.localhost',
    tenant=org,
    is_primary=True
)
```

### Demo Credentials
- **Admin (public):** admin@example.com / admin123
- **Demo user (demo schema):** demo@example.com / demo123

## Automatic Tenant Creation on Signup

### How it Works
When a user signs up, the system automatically:

1. **User provides Organization Name**
   - Custom field in signup form
   - Example: "First Baptist Church", "Grace Community", etc.

2. **Creates a new Organization (tenant)**
   - Schema name generated from organization name (e.g., `firstbaptistchurch`)
   - Organization name: User's input (e.g., "First Baptist Church")
   - Status: `trialing` (10 users max by default)

3. **Creates a Domain**
   - Format: `{schema_name}.localhost` (development)
   - In production: `{schema_name}.yourdomain.com`

4. **Creates OrganizationMembership**
   - Links user to organization
   - Role: `owner`
   - Stored in public schema

5. **Creates user in tenant schema**
   - Duplicates user data in the organization's schema
   - Allows tenant-specific data isolation

6. **Redirects after login**
   - User is automatically redirected to their organization's dashboard
   - URL: `http://{schema_name}.localhost:8000/dashboard/`

### User Flow Example

```
1. User visits: http://localhost:8000
2. Clicks "Sign Up"
3. Enters: 
   - Organization Name: First Baptist Church
   - Email: pastor@example.com
   - Password: ***
4. System creates:
   - Organization: schema_name='firstbaptistchurch', name="First Baptist Church"
   - Domain: firstbaptistchurch.localhost
   - Membership: pastor@example.com → 'firstbaptistchurch' (owner)
5. User verifies email
6. User logs in
7. Redirected to: http://firstbaptistchurch.localhost:8000/dashboard/
```

### Models

**OrganizationMembership** (in public schema)
- Links users to organizations
- Roles: `owner`, `admin`, `member`
- One user can belong to multiple organizations
- Primary organization = where user is owner, or most recent

### Customization

**Change default organization settings:**
```python
# In apps/accounts/signals.py
organization = Organization.objects.create(
    schema_name=schema_name,
    name=org_name,
    subscription_status='trialing',  # Change this
    max_users=10,  # Change this
)
```

**Change domain format:**
```python
# In apps/accounts/signals.py
# For production with real domains:
domain_name = f"{schema_name}.yourdomain.com"
```
