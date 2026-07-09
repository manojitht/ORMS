from django.db.models import Q
from django.urls import reverse

from .models import Notification


def notify(recipient, kind, title, body='', link_url='', dedupe_key=None,
           related_ticket=None, related_resource=None):
    """Create an in-app notification next to an existing email send.

    No-ops silently on recipient=None, mirroring how every ticket-lifecycle
    email call site already skips sending when it can't resolve a live
    Account (e.g. an employee with no portal access) -- this should never be
    the thing that raises where the email send wouldn't have.
    """
    if recipient is None:
        return None

    if dedupe_key is not None:
        notification, _created = Notification.objects.get_or_create(
            recipient=recipient, dedupe_key=dedupe_key,
            defaults=dict(
                kind=kind, title=title, body=body, link_url=link_url,
                related_ticket=related_ticket, related_resource=related_resource,
            ),
        )
        return notification

    return Notification.objects.create(
        recipient=recipient, kind=kind, title=title, body=body, link_url=link_url,
        related_ticket=related_ticket, related_resource=related_resource,
    )


def sync_sla_overdue_notifications(recipient, open_tickets):
    """Lazily backfill 'sla_overdue' notifications for `recipient` (an IT
    admin) from their already-computed `open_tickets` queryset -- there's no
    background job runner in this project, so this runs inline wherever that
    queryset already gets computed (the IT admin dashboard), matching the
    existing "compute fresh, no stored flag" approach `Ticket.is_overdue`
    itself already uses. Uses bulk_create against a single existing-keys
    lookup rather than get_or_create per ticket, so a dashboard visited daily
    by someone with dozens of overdue tickets doesn't re-query per ticket
    once the notifications already exist.
    """
    overdue_tickets = [t for t in open_tickets if t.is_overdue]
    if not overdue_tickets:
        return

    keys = {f'sla_overdue:{t.id}' for t in overdue_tickets}
    existing_keys = set(Notification.objects.filter(
        recipient=recipient, dedupe_key__in=keys).values_list('dedupe_key', flat=True))

    to_create = [
        Notification(
            company=recipient.company, recipient=recipient, kind='sla_overdue',
            title=f'Request {t.request_id} is overdue',
            body=f'{t.resource_label} has been waiting longer than expected.',
            link_url=reverse('tickets:view_selected_request_it_admin', args=[t.id]),
            related_ticket=t, dedupe_key=f'sla_overdue:{t.id}',
        )
        for t in overdue_tickets if f'sla_overdue:{t.id}' not in existing_keys
    ]
    if to_create:
        Notification.objects.bulk_create(to_create)


def sync_warranty_notifications(company):
    """Broadcasts warranty alerts to every active IT admin/superadmin in the
    company -- Resource has no owning IT admin (warranty counts on the
    dashboards are already company-wide, not per-assignee), so unlike SLA
    overdue this is inherently a broadcast rather than a single recipient.
    Same lazy, bulk_create-based backfill approach as the SLA sync above.
    """
    # Imported here (not at module level) to avoid a notifications -> resources
    # -> ... import at Django app-loading time; this module is only ever
    # imported from view code, well after all apps are registered, so it's
    # safe, but keeping model imports local to the functions that need them
    # keeps this service module's app-loading footprint minimal.
    from account.models import Account
    from resources.models import Resource

    resources = Resource.objects.filter(company=company, is_active=True, warranty_expiry_date__isnull=False)
    flagged = [(r, r.warranty_alert_level) for r in resources if r.warranty_alert_level]
    if not flagged:
        return

    recipients = list(Account.objects.filter(company=company, is_active=True).filter(
        Q(is_it_admin=True) | Q(is_superadmin=True)))
    if not recipients:
        return

    all_keys = {f'warranty:{r.id}:{level}' for r, level in flagged}
    existing_pairs = set(Notification.objects.filter(
        recipient__in=recipients, dedupe_key__in=all_keys
    ).values_list('recipient_id', 'dedupe_key'))

    to_create = []
    for recipient in recipients:
        for resource, level in flagged:
            key = f'warranty:{resource.id}:{level}'
            if (recipient.id, key) in existing_pairs:
                continue
            status_text = 'expired' if level == 'expired' else 'expiring soon'
            to_create.append(Notification(
                company=company, recipient=recipient, kind='warranty_alert',
                title=f'{resource.asset_id} warranty {level.replace("_", " ")}',
                body=f'{resource.model_name} warranty is {status_text}.',
                link_url=reverse('resources:view_resource', args=[resource.id]),
                related_resource=resource, dedupe_key=key,
            ))
    if to_create:
        Notification.objects.bulk_create(to_create)
