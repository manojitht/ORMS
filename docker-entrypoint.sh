#!/bin/sh
set -e

# Docker creates named volumes root-owned on first mount, but the app runs
# as non-root `appuser` — fix ownership before anything tries to write into
# staticfiles/media, then drop from root to appuser for the rest.
chown -R appuser:appuser /app/staticfiles /app/media 2>/dev/null || true

# Run at container start (not build time) so real env vars/secrets are
# available — prod settings raise if ALLOWED_HOSTS/SMTP aren't set, and
# those only exist at runtime via docker-compose's env_file.
gosu appuser python manage.py migrate --noinput
gosu appuser python manage.py collectstatic --noinput

exec gosu appuser "$@"
