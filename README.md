# Sukhra

Multi-tenant office resource & IT ticket management — track who has what, manage
requests from creation to completion, and keep every company's data completely
isolated from every other company's, all in one app.

Sukhra started as a single-company internal tool (formerly "ORMS" — Office
Resources Management System) and has since been generalized into a real
multi-tenant product: any company can sign up, configure its own resource
categories and custom attributes, and run its own IT asset lifecycle
independently of every other tenant on the same install.

## Table of contents

- [What it does](#what-it-does)
- [Tech stack](#tech-stack)
- [Architecture](#architecture)
- [Project structure](#project-structure)
- [Local development setup](#local-development-setup)
- [Running tests](#running-tests)
- [Docker](#docker)
- [Contributing](#contributing)

## What it does

### Roles

Sukhra has three roles per company, each with its own dashboard:

- **Superadmin** — owns the org: departments, teams, and user accounts
  (creates Manager and IT Administrator logins). Sees org-wide charts (org
  composition, user growth, company-wide resource/ticket rollups) and can
  export the user list as CSV.
- **Manager** — owns a team of employees (tracked people, not login
  accounts). Adds team members and raises tickets on their behalf. Exports
  completed tickets and the team roster as CSV.
- **IT Administrator** — owns the resource inventory: defines categories
  (with per-category custom attributes, e.g. a BitLocker key field for a
  "Laptop" category), adds physical or non-physical resources, and processes
  tickets end to end. Exports resources and completed tickets as CSV.

### The ticket lifecycle

Every request — `Pending → Processing → Completed` (or `Cancelled` at any
point) — is one of three types:

- **Request new** / **Replacement** — provisions a specific resource from a
  category; completing it allocates a real asset and marks it taken.
- **Support** — about something the employee *already has*. The manager
  picks which of the employee's assigned resources it concerns; on
  completion, IT doesn't retype anything — the resource's stored attribute
  values (e.g. a BitLocker key) are looked up and included automatically.

Every stage (created / approved / completed / cancelled) sends a branded
HTML email (with a plain-text fallback) to the relevant people.

### Multi-tenancy

Companies sign up self-serve, each getting an isolated tenant: their own
departments, teams, users, resource categories, resources, and tickets,
invisible to every other company on the same install. See
[Architecture](#architecture) for how isolation is enforced.

## Tech stack

| Layer | Choice |
|---|---|
| Language / framework | Python 3.11, Django 4.2 LTS |
| Package management | [`uv`](https://github.com/astral-sh/uv) (PEP 621 `pyproject.toml` + lockfile) |
| Database | SQLite (dev), PostgreSQL (prod, via `psycopg`) |
| Frontend | Server-rendered Django templates, Bootstrap 5 (vendored, not CDN), vanilla JS (no build step) |
| Charts | Chart.js (CDN) |
| Icons | [Lucide](https://lucide.dev) (CDN, SVG) |
| Fonts | IBM Plex Sans / IBM Plex Mono (Google Fonts) |
| Static files | WhiteNoise |
| Email | Django's email framework — console backend in dev, SMTP in prod; `EmailMultiAlternatives` for HTML+text emails |
| App server | Gunicorn |
| Reverse proxy | nginx (Docker only) |
| Testing | `pytest` + `pytest-django` + `factory_boy` |
| Linting | `ruff` |
| Containerization | Docker + docker-compose (app / db / nginx) |

No JS framework, no separate frontend build, no REST/GraphQL API layer —
this is intentionally a classic server-rendered Django app, which matches its
actual shape (CRUD-heavy, form-driven, no mobile client today).

## Design system

All design tokens (color, spacing, radius, shadow) and component CSS live in
one file: `sukhra/static/design-system.css`, loaded after the vendored `bootstrap.min.css`
and retheming it via Bootstrap's own CSS custom properties (`--bs-primary`,
`--bs-body-font-size`, etc.) wherever that's cheap, with real component rules
everywhere else.

- **Compact type scale.** Base body text runs at `.9rem` (14.4px) rather than
  Bootstrap's 16px default — tables, buttons, form controls, stat tiles, and
  the page-header heading are all sized deliberately dense to read as a
  focused product UI rather than a marketing page. New components should
  match this scale rather than falling back to Bootstrap's own (larger)
  defaults.
- **Icons: Lucide, not Boxicons.** Every icon in the app is a real inline SVG
  via `<i data-lucide="icon-name"></i>` + `lucide.createIcons()` (called once
  on `DOMContentLoaded` in `sukhra/static/script.js`), not an icon font —
  crisper at small sizes and one consistent stroke style everywhere, instead
  of mixing outline/solid variants. When adding a new icon, check the name
  exists at [lucide.dev/icons](https://lucide.dev/icons) first — a
  nonexistent name silently leaves a blank space (Lucide just can't find it
  to render), it won't error.
- **Responsive by default.** Every page uses Bootstrap's grid (`col-md-*`,
  `col-lg-*`) and the navbar's built-in `navbar-toggler`/`collapse` for
  mobile — verified via Playwright screenshots at 375px (mobile), 768px
  (tablet/iPad portrait), 1024px (iPad landscape/small laptop), and 1440px
  (desktop) across representative dashboard/table/form pages. Wide tables
  scroll horizontally within their own `.table-responsive` container on
  narrow screens rather than breaking the page layout — this is intentional
  (a real card-based mobile table alternative would be a much larger,
  per-template change, not a token-level one).

## Architecture

### Apps

| App | Owns |
|---|---|
| `companies` | `Company` (the tenant), plus the tenant-isolation machinery (see below) |
| `account` | `Account` — the login/auth model (Superadmin / Manager / IT Admin) |
| `department`, `team` | Org structure each company is scoped into |
| `employees` | `Employee` — a tracked person who does **not** log in (distinct from `Account`) |
| `resources` | `Category` (with custom attribute schema), `Resource`, `ResourceTaken`, `OtherAccessories` |
| `tickets` | `Ticket` — the request/support lifecycle |

### Multi-tenancy: how isolation is enforced

Row-level isolation, shared database/schema. Every tenant-scoped model
subclasses `TenantModel` (`companies/models.py`):

```python
class TenantModel(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    objects = TenantManager()      # auto-scoped
    all_objects = models.Manager() # explicit escape hatch
```

- A `contextvars`-based "current company" context (`companies/context.py`)
  is set once per request by `CurrentCompanyMiddleware`, from
  `request.user.company`.
- `TenantManager.get_queryset()` auto-filters every query to that company —
  and **fails closed**: with no context set, it returns `.none()`, not every
  company's rows. A missing middleware/context bug shows up as an empty
  page, not a cross-tenant data leak.
- `TenantModel.save()` auto-stamps `company` on create if unset — the
  write-side mirror of the same guarantee.
- `all_objects` is the deliberate, narrow escape hatch used only where no
  request context exists yet (signup) or admin tooling needs every row.

**`Account` is the one documented exception.** Django requires
`USERNAME_FIELD` to be globally unique (the `auth.E003` check), so
`Account.peoplesoft_id` stays globally unique rather than per-company, and
`Account.objects` stays an **unscoped** manager — every authenticated view
that queries `Account` filters by `company=` explicitly itself. This is why
login only needs a PeopleSoft ID + password, with no separate company
selector: the ID alone already disambiguates the company.

### Per-category custom attributes

Rather than hardcoding fields onto `Resource` for one company's specific
hardware (the original design assumed Windows laptops with a BitLocker key),
`Category.attribute_schema` is a small admin-defined JSON schema
(`[{"key": "bitlocker_key", "label": "BitLocker Key"}, ...]`), and
`Resource.attribute_values` stores the actual values. Add/Edit Resource forms
render every possible attribute field once and a small vanilla-JS snippet
shows only the fields belonging to the selected category — no page reload,
no JS build step.

### Settings

Split by environment (`sukhra/settings/{base,dev,prod}.py`), driven by
`django-environ`. `dev.py` defaults to SQLite + console email backend with
zero required env vars; `prod.py` requires `DATABASE_URL` /
`DJANGO_ALLOWED_HOSTS` / SMTP credentials and turns on Django's `SECURE_*`
hardening flags.

## Project structure

```
sukhra/                  # Django project package (settings, root urls, static/, csv_utils.py)
account/                 # Auth, login, dashboards, add/edit users
companies/               # Company model, TenantModel/TenantManager, signup flow
department/  team/       # Org structure
employees/               # Tracked (non-login) people
resources/               # Categories, resources, ResourceTaken
tickets/                 # Ticket lifecycle
templates/               # Shared + per-role templates (account/, manager/, it_admin/, superadmin/, includes/)
templates/account/emails/# Branded HTML email templates
factories.py             # Shared factory_boy test factories, used across every app's tests
docker-compose.yml       # app + db (Postgres) + nginx
```

## Local development setup

```bash
# 1. Install dependencies
uv sync

# 2. Configure environment
cp .env.example .env
# dev.py works with an empty .env — only fill in EMAIL_* if you want to test
# real outgoing mail instead of the console backend.

# 3. Apply migrations
uv run manage.py migrate

# 4. Seed a demo company so there's actually something to look at
uv run manage.py seed_demo_data

# 5. Run the dev server
uv run manage.py runserver
```

### Seeding demo data

`seed_demo_data` creates one fully-populated company — departments/teams,
one account per role, two resource categories with custom attributes
(Laptops with a BitLocker key, Phones with an IMEI), a handful of resources,
one employee, and tickets covering every lifecycle state (pending,
processing, completed — both a "Request new" and a "Support" ticket —  and
cancelled). It's what every screenshot in this README's own development was
generated from.

```bash
uv run manage.py seed_demo_data              # creates company code "demo"
uv run manage.py seed_demo_data --reset      # wipes and recreates it
uv run manage.py seed_demo_data --company-code acme --company-name "Acme Inc"
```

It refuses to overwrite an existing company with the same code unless you
pass `--reset`, so it's safe to run again without wondering whether it just
duplicated everything. Login credentials print at the end of the command —
they're also fixed (not random) so you don't have to go looking for them
twice:

| Role | PeopleSoft ID | Password |
|---|---|---|
| Superadmin | `10000001` | `SuperPass1!` |
| Manager | `10000002` | `ManagerPass1!` |
| IT Administrator | `10000003` | `ITAdminPass1!` |

Alternatively, sign up a fresh company by hand at `/companies/signup/` if
you want to test that flow specifically rather than starting pre-seeded.

Emails print to the terminal running `runserver` (console backend) rather
than sending anywhere — see `templates/account/emails/` for the HTML
templates if you want to preview one directly:

```bash
uv run manage.py shell -c "
from django.template.loader import render_to_string
html = render_to_string('account/emails/account_confirmation_email.html', {
    'user': Account.objects.first(), 'domain': '127.0.0.1:8000', 'uid': 'x', 'token': 'x',
})
open('/tmp/preview.html', 'w').write(html)
"
open /tmp/preview.html
```

## Running tests

```bash
uv run pytest          # full suite
uv run pytest resources/  # one app
uv run ruff check .    # lint
```

Tests use `pytest-django` + `factory_boy` (`factories.py`). Every factory
threads `company=` through nested `SubFactory` relationships via
`factory.SelfAttribute('..company')`, so a plain `ManagerAccountFactory()`
call produces one coherent single-tenant object graph — pass an explicit
`company=` to test cross-tenant behavior deliberately.

## Docker

```bash
cp .env.example .env   # fill in POSTGRES_*, EMAIL_*, DJANGO_SECRET_KEY
docker compose up --build
```

Three services: `db` (Postgres 16), `app` (Gunicorn, migrates + collects
static at container start, runs as non-root), `nginx` (serves `/static/` and
`/media/` directly, reverse-proxies everything else). `nginx.conf` does
**not** terminate TLS — for a real internet-facing deployment, put a
TLS-terminating layer in front (cloud LB/CDN, or nginx extended with a real
certificate) and set `DJANGO_SECURE_SSL_REDIRECT=True`.

## Contributing

This is an actively evolving product, not a finished one — expect the
schema and UI to keep shifting. A few practices that keep that safe:

### Before opening a PR

- `uv run pytest` passes locally, full suite (not just the app you touched —
  cross-app coupling here is real, e.g. `account` reads from `resources` and
  `tickets` for dashboard counts).
- `uv run manage.py makemigrations --check --dry-run` is clean, or your
  migration is included and named descriptively (not `0007_auto_...`).
- `uv run ruff check .` is clean.
- If you touched a tenant-scoped model, add a test proving isolation still
  holds (a second company can't see/guess-ID into the new data) — this is
  the single most important category of regression in this codebase.
- If you touched an email template, actually render it (see
  [Local development setup](#local-development-setup)) rather than trusting
  the diff — email HTML is unusually easy to break silently.

### Branching & commits

- Branch names: `<type>/<short-description>` (`fix/ticket-completion-email`,
  `feat/department-csv-export`).
- Commit messages explain **why**, not just what — the diff already shows
  what changed.
- Prefer several small, reviewable commits over one large one; don't squash
  away the history of a non-trivial change before opening the PR.

### Schema changes

- Never hand-edit a migration to "fix" it after the fact — generate a new
  one.
- Additive changes (new nullable field, new table) are low-risk. Anything
  that removes/renames a field or tightens a constraint on a table that
  might have real data needs a two-step migration (add nullable → backfill →
  make required), not a single destructive step.
- Any new tenant-scoped model must subclass `TenantModel`, not
  `models.Model` directly — that's what makes isolation automatic instead of
  something every future view has to remember to add.

### Code review expectations

- A reviewer should be able to tell *why* a change was made from the PR
  description, not have to reverse-engineer it from the diff.
- Flag anything that adds a manual `.filter(company=...)` where a
  `TenantModel`/`TenantManager` could have made it automatic instead — that
  pattern is exactly how cross-tenant leaks happen.
- Prefer asking "why" over rewriting silently — this codebase has a lot of
  organically-grown behavior (e.g. `Account` being the one unscoped-manager
  exception) that looks like a bug until you know the constraint behind it.
