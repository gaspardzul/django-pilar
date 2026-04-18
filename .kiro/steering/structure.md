# Project Structure

## Directory Layout

```
alaba-plus/
├── core/                    # Django project configuration
│   ├── settings.py          # All settings via environment variables
│   ├── urls.py              # Public tenant URLs (landing, signup, login)
│   ├── urls_tenants.py      # Tenant-specific URLs (dashboard, features)
│   ├── wsgi.py
│   └── asgi.py
├── apps/                    # Django applications
│   ├── accounts/            # SHARED - User model and authentication
│   ├── organizations/       # SHARED - Tenant model and domains
│   ├── dashboard/           # TENANT - Dashboard, profile, settings
│   ├── landing/             # TENANT - Public pages
│   ├── subscriptions/       # TENANT - Stripe integration
│   └── business/            # TENANT - Church management (members, ministries, families, events)
├── templates/               # HTML templates
│   ├── base.html            # Public layout (nav + footer)
│   ├── account/             # django-allauth templates (20 styled templates)
│   ├── dashboard/           # Dashboard layout + pages
│   ├── landing/             # Home, features, pricing
│   └── subscriptions/       # Stripe checkout
├── static/                  # Static assets
│   ├── css/                 # Design system CSS
│   └── js/                  # JavaScript files
├── staticfiles/             # Collected static files (generated)
├── .kiro/                   # Kiro configuration
│   └── steering/            # Steering documents
├── .env                     # Environment variables (not in git)
├── .env.example             # Environment template
├── Makefile                 # Development commands
├── Procfile                 # Deployment configuration
├── requirements.txt         # Python dependencies
└── pyproject.toml           # Ruff configuration
```

## App Organization

### Shared Apps (Public Schema)

Available to all tenants, stored in public schema:

- **accounts**: CustomUser model (email-only), OrganizationMembership, authentication
- **organizations**: Organization (tenant) model, Domain model

### Tenant Apps (Isolated Schemas)

Isolated per tenant schema:

- **dashboard**: User dashboard, profile, settings, subscription management
- **landing**: Public pages (home, features, pricing)
- **subscriptions**: Stripe integration, webhooks, checkout
- **business**: Church management (members, ministries, families, events)

## Key Conventions

### Multi-Tenancy Architecture

- **Schema Routing**: Subdomains map to tenant schemas (e.g., `demo.localhost` → `demo` schema)
- **Public Schema**: Contains shared data (users, organizations)
- **Tenant Schemas**: Isolated data per organization
- **Schema Context**: Use `from django_tenants.utils import schema_context` to switch schemas

### URL Routing

- **Public URLs** (`core/urls.py`): Landing pages, signup, login, admin
- **Tenant URLs** (`core/urls_tenants.py`): Dashboard, app features, tenant-specific views

### Models

- **User References**: Always use `settings.AUTH_USER_MODEL` for ForeignKey/OneToOneField
- **User Queries**: Use `get_user_model()` from `django.contrib.auth`
- **Tenant Model**: `apps.organizations.Organization` with `schema_name` field
- **Domain Model**: `apps.organizations.Domain` for subdomain routing

### Views

- **Style**: Function-based views preferred
- **Decorators**: Use `@login_required` and `@require_http_methods(['GET', 'POST'])`
- **URL Namespaces**: App-specific (e.g., `landing:home`, `dashboard:profile`)
- **Messages**: Use Django messages framework for user feedback
- **Redirects**: Return `redirect('namespace:view_name')` after POST

### Templates

- **Base Templates**: 
  - `templates/base.html` for public pages
  - `templates/dashboard/base.html` for authenticated pages
- **Design System**: Monochromatic (black/white/gray), Space Grotesk font, uppercase tracking
- **CSP**: All external scripts/styles use `nonce="{{ csp_nonce }}"`
- **Partials**: Use `{% partialdef name inline %}` for reusable components

### Background Tasks

- **Decorator**: Use `@task` from `django.tasks`
- **Enqueue**: Call `.enqueue(param=value)` on task function
- **Location**: Task definitions in `apps/dashboard/tasks.py`
- **Use Cases**: Email sending, async operations

### Static Files

- **Development**: Files served from `static/` directories
- **Production**: Collected to `staticfiles/` via `collectstatic`, served by WhiteNoise
- **CSS**: Custom design system in `static/css/design-system.css`
- **JS**: Minimal JavaScript, mostly Alpine.js and HTMX

### Code Style

- **Linter**: Ruff with Django-specific rules
- **Quotes**: Single quotes preferred
- **Line Length**: 120 characters max
- **Imports**: Sorted with isort, `apps` and `core` as first-party
- **Format**: Run `make format` before committing

### Testing

- **Location**: `tests.py` in each app directory
- **Run**: `make test` or `python manage.py test`
- **Coverage**: Landing pages, auth flows, dashboard views, models

### Migrations

- **Shared Apps**: `python manage.py migrate_schemas --shared`
- **Tenant Apps**: `python manage.py migrate_schemas`
- **Both**: `make migrate` (runs makemigrations + migrate)

## File Naming

- **Models**: Singular, PascalCase (e.g., `Member`, `Ministry`, `Family`)
- **Views**: Lowercase with underscores (e.g., `member_detail`, `ministry_create`)
- **Templates**: Lowercase with underscores, organized by app and feature
- **URLs**: Lowercase with hyphens (e.g., `/members/`, `/ministries/create/`)
