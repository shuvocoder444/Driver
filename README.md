
# Driver

## Local setup

Install dependencies, apply migrations, then start the development server:

```powershell
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Run the automated checks and tests with:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

## Deployment configuration

Set `DJANGO_DEBUG=false`, a unique random `DJANGO_SECRET_KEY`, and comma-separated
`DJANGO_ALLOWED_HOSTS` before deployment. Configure `DJANGO_CSRF_TRUSTED_ORIGINS`
with the exact HTTPS origins used by the site. HTTPS redirection and secure
session/CSRF cookies are enabled when debug mode is off. Set
`DJANGO_SECURE_HSTS_SECONDS` only after HTTPS is working; enable
`DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS` and `DJANGO_SECURE_HSTS_PRELOAD` only if
every affected domain is permanently HTTPS-only.
