# Arivom

Multi-tenant office resource & IT ticket management — track who has what, manage
requests from creation to completion, and keep every company's data completely
isolated from every other company's, all in one app.

Arivom started as a single-company internal tool (formerly "ORMS" — Office
Resources Management System) and has since been generalized into a real
multi-tenant product: any company can sign up, configure its own resource
categories and custom attributes, and run its own IT asset lifecycle
independently of every other tenant on the same install.

Beyond the core ticket/resource loop, Arivom also covers: bulk CSV import of
resources, warranty/lease expiry alerts, QR/barcode asset tagging for
scan-to-issue/return, SLA response/resolution-time tracking with overdue
flags, and an employee self-service portal (raise your own requests, see your
own gear) gated behind manager approval before IT ever sees them.

## Table of contents

- [What it does](#what-it-does)
- [End-to-end workflow](#end-to-end-workflow)
- [Tech stack](#tech-stack)
- [Architecture](#architecture)
- [Project structure](#project-structure)
- [Local development setup](#local-development-setup)
- [Running tests](#running-tests)
- [Docker](#docker)
- [Contributing](#contributing)

## What it does

### Roles

Arivom has four roles per company, each with its own dashboard:

- **Superadmin** — owns the org: departments, teams, and user accounts
  (creates Manager and IT Administrator logins). Sees org-wide charts (org
  composition, user growth, company-wide resource/ticket rollups, company-wide
  SLA stats) and can export the user list as CSV.
- **Manager** — owns a team of employees. Adds team members, raises tickets
  on their behalf, and optionally grants them their own self-service portal
  login. Reviews and approves/denies requests employees raise themselves
  before they reach IT. Exports completed tickets and the team roster as CSV.
- **IT Administrator** — owns the resource inventory: defines categories
  (with per-category custom attributes, e.g. a BitLocker key field for a
  "Laptop" category), adds physical or non-physical resources, tracks
  warranty/lease expiry, generates QR labels for physical assets, and
  processes tickets end to end. Sees response/resolution-time and overdue
  stats on their dashboard. Exports resources and completed tickets as CSV.
- **Employee** — a tracked team member. Doesn't log in by default (still
  just an `Employee` record a Manager manages), but can optionally be granted
  a lightweight self-service login: raise their own requests, see their own
  assigned resources, and track request status — without needing their
  manager to do it for them. See [Employee self-service](#employee-self-service)
  for how this is wired up.

### The ticket lifecycle

Every request — `Pending → Processing → Completed` (or `Cancelled` at any
point) — is one of three types:

- **Request new** / **Replacement** — provisions a specific resource from a
  category; completing it allocates a real asset and marks it taken.
- **Support** — about something the employee *already has*. The manager
  picks which of the employee's assigned resources it concerns; on
  completion, IT doesn't retype anything — the resource's stored attribute
  values (e.g. a BitLocker key) are looked up and included automatically.

A request an **Employee** raises themselves (via their self-service portal)
starts one step earlier — `Pending Manager Approval` — and only advances to
the regular `Pending` queue IT admins see once their manager approves it
(denying it moves straight to `Cancelled`, with an optional reason emailed
back to the employee). Manager-raised requests skip this step entirely and
start at `Pending` exactly as before.

Every stage (submitted / needs approval / approved / denied / completed /
cancelled) sends a branded HTML email (with a plain-text fallback) to the
relevant people.

**SLA tracking.** Each `Ticket` records `created_on`, `processing_started_on`
(stamped the moment it's approved into Processing), and `completed_on` — so
average response time (created → processing) and resolution time
(processing → completed) can be computed directly in the database with
`Avg(F(...) - F(...))`, no extra bookkeeping. A ticket still open past a
hardcoded threshold (`tickets/models.py`: `SLA_HOURS_TO_START_PROCESSING`,
`SLA_DAYS_TO_COMPLETE`) shows an "Overdue" badge on the IT admin's request
lists — there's no per-category/per-company configuration for these yet, and
no background job computes them proactively; it's all derived at request
time from the two timestamps above.

### Resource lifecycle extras

- **Bulk CSV import.** Symmetric with the existing CSV export: upload a CSV
  (template downloadable from the same page) and each row becomes a
  `Resource`. Bad rows (unknown category, missing required field, duplicate
  asset id) are skipped individually with a reason shown back to you — one
  malformed row doesn't sink the rest of the batch.
- **Warranty/lease expiry alerts.** An optional `warranty_expiry_date` on
  `Resource` drives an "expiring soon" / "expired" status pill on resource
  lists, the detail page, and IT admin/Superadmin dashboard tiles that link
  straight to a dedicated alerts page. Computed at request time from a
  hardcoded lead-time window (`resources/models.py`:
  `WARRANTY_ALERT_WINDOW_DAYS`), not a scheduled job — there's no background
  task runner in this project (see [Tech stack](#tech-stack)), so there's no
  proactive email digest yet, just an always-current on-page indicator.
- **QR/barcode tagging.** Every resource has a generated QR code (and a
  printable label) encoding a scan-action URL for that asset. Scanning it
  routes based on the resource's current availability: an *Available*
  resource shows Processing tickets requesting that category with a
  one-click "complete with this asset" action; a *Taken* resource shows a
  return-confirmation form. Both paths call straight into the existing
  `complete_processing_request` / `mark_returned` views — scanning removes
  the manual asset-id typing step, it doesn't introduce a second, parallel
  way to hand out or take back a resource, so every `ResourceTaken` row
  still traces back to a real `Ticket`.

### Multi-tenancy

Companies sign up self-serve, each getting an isolated tenant: their own
departments, teams, users, resource categories, resources, and tickets,
invisible to every other company on the same install. See
[Architecture](#architecture) for how isolation is enforced.

## End-to-end workflow

A concrete walkthrough of one full loop, start to finish, across every role:

1. **A company signs up.** Anyone visiting `/companies/signup/` creates a new
   `Company` plus its first **Superadmin** account, with zero setup required
   from an existing tenant — this is what actually creates the isolated
   tenant every later step happens inside.
2. **Superadmin builds the org.** Creates `Department`s and `Team`s, then
   creates a **Manager** and an **IT Administrator** account for each team
   that needs one (`account:add_user_page`) — each new account is `is_active=False`
   until its owner clicks the activation link in the email they're sent.
3. **IT Administrator sets up the resource catalog.** Defines `Category`s
   (e.g. "Laptops"), each with its own custom attribute schema (e.g. a
   BitLocker key field) and a `tracks_physical_asset` flag (physical units
   vs. license-only categories), then adds actual `Resource` rows — either
   one at a time, or in bulk via CSV import. Physical resources can get a
   `warranty_expiry_date` and a generated QR label to print and stick on the
   device.
4. **Manager builds their team.** Adds `Employee` records for each person on
   their team, optionally checking "grant portal access" to give that person
   their own self-service login (or grants it retroactively later from the
   team member's detail page).
5. **A request gets raised**, one of two ways:
   - The **Manager** raises it directly on the employee's behalf
     (`tickets:create_request`) — it starts at `Pending`, assigned to a
     random `is_it_admin` account in the same company.
   - The **Employee** raises it themselves (`tickets:create_request_employee`)
     — it starts at `Pending Manager Approval` and emails their manager. The
     manager approves it (→ `Pending`, same as the manager-raised path from
     here on) or denies it (→ `Cancelled`, with an optional reason emailed
     back).
6. **IT Administrator processes it.** Approves it into `Processing`
   (`processing_started_on` is stamped here, starting the SLA clock) and
   works the request, then completes it — either through the normal
   completed-request form, or by scanning the target resource's QR label,
   which shows only the Processing tickets that resource could fulfil and
   completes it in one tap. Completing:
   - a **Request new**/**Replacement** ticket allocates a real `Resource`,
     flips it to `Taken`, and creates a `ResourceTaken` row linking it to the
     employee;
   - a **Support** ticket looks up the employee's already-assigned resource
     and its stored attribute values automatically, no retyping.
7. **The employee has the resource.** They (or their manager) can see it
   under "My Resources"/"Resources Taken", IT can see it under "In & Outs",
   and the Superadmin sees it rolled up company-wide on their dashboard.
8. **Eventually, it's returned.** Either through the manager's "Mark
   Returned" flow on the employee's profile, or by scanning the resource's
   QR label again (now routed to a return-confirmation form instead, since
   it's `Taken`) — either way, a reason is recorded (leaving the company,
   swapping for a better spec, damaged, software issue) and the resource
   goes back to `Available` (or `Configuration` if it needs attention first).
9. **Along the way**, every stage sends a branded email to whoever needs to
   know, response/resolution-time and overdue stats accumulate on the IT
   Admin's and Superadmin's dashboards, and warranty alerts surface on their
   own schedule regardless of ticket activity — none of this needs a
   separate reporting step, it's all derived from the same rows as they're
   written.

## Tech stack

| Layer | Choice |
|---|---|
| Language / framework | Python 3.11, Django 4.2 LTS |
| Package management | [`uv`](https://github.com/astral-sh/uv) (PEP 621 `pyproject.toml` + lockfile) |
| Database | SQLite (dev), PostgreSQL (prod, via `psycopg`) |
| Frontend | Server-rendered Django templates, Bootstrap 5 (vendored, not CDN), vanilla JS (no build step) |
| Charts | Chart.js (CDN), colors read from the design system's CSS custom properties rather than hardcoded hex |
| Icons | [Lucide](https://lucide.dev) (CDN, SVG) |
| Fonts | IBM Plex Sans / IBM Plex Mono (Google Fonts) |
| QR codes | [`qrcode`](https://pypi.org/project/qrcode/) (server-side generation) + [html5-qrcode](https://github.com/mebjas/html5-qrcode) (CDN, camera-based scanning in the browser) |
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
one file: `arivom/static/design-system.css`, loaded after the vendored `bootstrap.min.css`
and retheming it via Bootstrap's own CSS custom properties (`--bs-primary`,
`--bs-body-font-size`, etc.) wherever that's cheap, with real component rules
everywhere else. Palette: sky blue / mustard yellow / white, with a dark-navy
sidebar for contrast.

- **App shell: sidebar + topbar.** Every authenticated page (`templates/base.html`)
  renders a fixed left sidebar (role-specific nav, active-state highlighting
  via `account/templatetags/nav_extras.py`'s `nav_active` tag) and a slim
  topbar (breadcrumb slot + avatar/user-menu dropdown), collapsing to a
  Bootstrap `offcanvas` panel below the `lg` breakpoint — no custom JS, just
  Bootstrap's own `data-bs-toggle="offcanvas"`. Public/unauthenticated pages
  (welcome, login, signup) are standalone documents that don't use this shell
  at all.
- **Compact type scale.** Base body text runs at `.9rem` (14.4px) rather than
  Bootstrap's 16px default — tables, buttons, form controls, stat tiles, and
  the page-header heading are all sized deliberately dense to read as a
  focused product UI rather than a marketing page. New components should
  match this scale rather than falling back to Bootstrap's own (larger)
  defaults.
- **Icons: Lucide, not Boxicons.** Every icon in the app is a real inline SVG
  via `<i data-lucide="icon-name"></i>` + `lucide.createIcons()` (called once
  on `DOMContentLoaded` in `arivom/static/script.js`), not an icon font —
  crisper at small sizes and one consistent stroke style everywhere, instead
  of mixing outline/solid variants. When adding a new icon, check the name
  exists at [lucide.dev/icons](https://lucide.dev/icons) first — a
  nonexistent name silently leaves a blank space (Lucide just can't find it
  to render), it won't error.
- **Reusable component classes.** `.table-toolbar` (search/filter row + a
  primary action), `.empty-state` (icon + title + helper text, via
  `templates/includes/empty_state.html`), `.form-card`/`.form-card--wide`
  (centered form containers, 640px/720px), and `.status-pill--*` (good /
  info / warn / danger / neutral / muted) cover the vast majority of new
  list/form/detail pages — check these before writing new one-off CSS.
- **Responsive by default.** Every page uses Bootstrap's grid (`col-md-*`,
  `col-lg-*`) — verified via Playwright screenshots at 375px (mobile), 768px
  (tablet/iPad portrait), 1024px (iPad landscape/small laptop), and 1440px
  (desktop) across representative dashboard/table/form pages, with particular
  attention at the `lg` breakpoint where the sidebar swaps to the offcanvas
  panel. Wide tables scroll horizontally within their own `.table-responsive`
  container on narrow screens rather than breaking the page layout — this is
  intentional (a real card-based mobile table alternative would be a much
  larger, per-template change, not a token-level one).

## Architecture

### Apps

| App | Owns |
|---|---|
| `companies` | `Company` (the tenant), plus the tenant-isolation machinery (see below) |
| `account` | `Account` — the login/auth model (Superadmin / Manager / IT Admin / self-service Employee) |
| `department`, `team` | Org structure each company is scoped into |
| `employees` | `Employee` — a tracked person, distinct from `Account`, optionally linked to one via `Account.employee_profile` for self-service login |
| `resources` | `Category` (with custom attribute schema), `Resource` (incl. `warranty_expiry_date`), `ResourceTaken`, `OtherAccessories` |
| `tickets` | `Ticket` — the request/support lifecycle, incl. SLA timestamps and the employee-approval status |

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

### Employee self-service

`Employee` (a tracked person) and `Account` (the login model) are, by
design, two separate models — `Employee.peoplesoft_id` is only unique
*per company*, while `Account.peoplesoft_id` must be globally unique (see
the `Account` exception above), so `Employee` itself can never be the login
model. Instead, `Account` gained a fourth role flag (`is_employee`) and a
nullable `OneToOneField` to `Employee` (`Account.employee_profile`,
`on_delete=SET_NULL`, `related_name='account'`) — `Account` owns the link
since it's the actor/auth model, and `employee.account` is how a template
checks "does this person have portal access yet".

- **Provisioning**: a Manager can grant portal access inline when adding a
  new team member, or retroactively from an existing team member's detail
  page. Either path calls `MyManagerAccount.create_employee(...)` (mirrors
  `create_manager`/`create_IT_admin`) and reuses the same activation-email
  flow every other role already goes through. The temp-password generator
  and activation-email sender were pulled out into
  `arivom/account_provisioning.py` so both `account/views.py` and
  `employees/views.py` share one implementation.
- **Offboarding**: hard-deleting an `Employee` with a linked `Account`
  deactivates that `Account` first (`is_active=False`) — `employee_profile`
  being `SET_NULL` would otherwise silently null the FK and leave an
  orphaned *active* login behind.
- **Cross-tenant id collisions**: because `Employee.peoplesoft_id` is only
  unique per company but `Account.peoplesoft_id` is global, two different
  companies' employees can occasionally collide on id when granting portal
  access. This surfaces as a plain "already taken" message (same pattern as
  `add_user_page`'s existing collision check) — it doesn't redesign
  `USERNAME_FIELD`.

### Settings

Split by environment (`arivom/settings/{base,dev,prod}.py`), driven by
`django-environ`. `dev.py` defaults to SQLite + console email backend with
zero required env vars; `prod.py` requires `DATABASE_URL` /
`DJANGO_ALLOWED_HOSTS` / SMTP credentials and turns on Django's `SECURE_*`
hardening flags.

## Project structure

```
arivom/                  # Django project package (settings, root urls, static/, csv_utils.py, account_provisioning.py)
account/                 # Auth, login, dashboards, add/edit users (incl. self-service Employee accounts)
companies/               # Company model, TenantModel/TenantManager, signup flow
department/  team/       # Org structure
employees/               # Tracked people; optionally linked to an Account for self-service login
resources/               # Categories, resources (incl. warranty tracking), ResourceTaken, QR/scan views
tickets/                 # Ticket lifecycle, incl. employee-approval flow and SLA tracking
templates/               # Shared + per-role templates (account/, manager/, it_admin/, superadmin/, employee/, includes/)
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

It doesn't currently seed the newer optional bits — no resource has a
`warranty_expiry_date` set, no employee has self-service portal access, and
there's no `Pending Manager Approval` ticket — so to see those in action,
grant portal access to the seeded employee from a Manager's team page, log
in as them, and raise a request; or set a warranty date while editing a
seeded resource as the IT Administrator.

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
