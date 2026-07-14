# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=arivom.settings.prod

# libpq5 for psycopg (Postgres) at runtime. gosu to drop from root to
# appuser in the entrypoint, after fixing up volume-mount ownership.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 gosu \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /usr/local/bin/

WORKDIR /app

# Dependencies first so this layer caches across code-only changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app

# Stays root here — docker-entrypoint.sh chowns the (root-owned-by-default)
# staticfiles/media volume mounts, then drops to appuser via gosu before
# running anything Django-related.

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "arivom.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
