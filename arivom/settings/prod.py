"""Production settings. Requires DJANGO_ALLOWED_HOSTS, DATABASE_URL and SMTP
env vars to be set — see .env.example."""

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

if not ALLOWED_HOSTS:  # noqa: F405
    raise ValueError('DJANGO_ALLOWED_HOSTS must be set in production')

if not (EMAIL_HOST_USER and EMAIL_HOST_PASSWORD):  # noqa: F405
    raise ValueError('EMAIL_HOST_USER and EMAIL_HOST_PASSWORD must be set in production')

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Serve collected static files directly from the app via whitenoise,
# in front of/alongside nginx. Requires `manage.py collectstatic` at build time.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# HTTPS/TLS hardening — nginx terminates TLS in front of this app.
SECURE_SSL_REDIRECT = env.bool('DJANGO_SECURE_SSL_REDIRECT', default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int('DJANGO_SECURE_HSTS_SECONDS', default=60 * 60 * 24 * 30)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
