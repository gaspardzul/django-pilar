# Tech Stack

## Core Technologies

- **Backend**: Django 6.0, Python 3.12
- **Database**: PostgreSQL (required for multi-tenancy), SQLite (dev fallback)
- **Multi-Tenancy**: django-tenants (schema-based isolation)
- **Authentication**: django-allauth (email-only, no username field)
- **Payments**: Stripe (Payment Methods API)
- **Frontend**: Tailwind CSS (CDN), Alpine.js, HTMX
- **Static Files**: WhiteNoise
- **Server**: Gunicorn
- **Background Tasks**: Django 6.0 native `@task()` decorator
- **Linting**: Ruff

## Key Dependencies

```
Django>=6.0,<6.1
django-allauth
django-tenants
django-htmx
django-crispy-forms
crispy-tailwind
stripe
dj-database-url
psycopg[binary]
whitenoise
gunicorn
python-dotenv
ruff
```

## Django 6.0 Features Used

- **Background Tasks**: `@task` decorator with `.enqueue()` for async email sending
- **Content Security Policy**: Built-in CSP middleware with nonce support (`{{ csp_nonce }}`)
- **Template Partials**: `{% partialdef %}` and `{% partial %}` for reusable components

## Common Commands

### Development

```bash
make install    # Create virtualenv and install dependencies
make run        # Start development server (localhost:8000)
make migrate    # Run makemigrations + migrate
make test       # Run test suite
make lint       # Lint with ruff
make format     # Format with ruff
make clean      # Remove __pycache__ files
```

### Database & Tenants

```bash
make seed                                    # Populate demo data
python manage.py migrate_schemas --shared    # Migrate public schema only
python manage.py migrate_schemas             # Migrate all tenant schemas
python create_tenants.py                     # Create public + demo tenants
python create_superuser.py                   # Create admin users
python reset_db.py                           # Reset PostgreSQL database
```

### Tenant-Specific Commands

```bash
python manage.py tenant_command <command> --schema=<schema_name>
```

## Environment Variables

Required in `.env` (copy from `.env.example`):

```bash
# Core
SECRET_KEY=your-secret-key
DEBUG=True

# Database (PostgreSQL required for multi-tenancy)
DATABASE_URL=postgres://user:password@localhost:5432/dbname

# Stripe
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...

# Email (optional, defaults to console backend)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## Ruff Configuration

Located in `pyproject.toml`:

- Target: Python 3.12
- Line length: 120
- Quote style: single quotes
- Import sorting: isort with `apps` and `core` as first-party
- Rules: pycodestyle, pyflakes, flake8-bugbear, flake8-django

## Testing

Run tests with `make test` or `python manage.py test`. Currently 16 tests covering:
- Landing pages
- Authentication flows
- Dashboard views
- Model functionality
