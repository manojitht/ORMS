"""Local development settings."""

from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Never send real email in local dev — print to the console instead.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
