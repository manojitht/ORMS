from django.db import models

from account.models import Account
from companies.models import TenantModel

# Lucide icon name + status-pill color variant per notification kind, reusing
# the existing --status-good/info/warn/danger tokens rather than inventing
# new colors -- see design-system.css's .status-pill for the same palette.
KIND_ICONS = {
    'ticket_created': 'plus-circle',
    'ticket_approval_needed': 'user-check',
    'ticket_approved': 'check-circle',
    'ticket_denied': 'x-circle',
    'ticket_cancelled': 'x-circle',
    'ticket_processing': 'loader',
    'ticket_completed': 'check-circle',
    'resource_returned': 'undo-2',
    'warranty_alert': 'shield-alert',
    'sla_overdue': 'alarm-clock',
}
KIND_COLORS = {
    'ticket_created': 'info',
    'ticket_approval_needed': 'info',
    'ticket_approved': 'good',
    'ticket_denied': 'danger',
    'ticket_cancelled': 'danger',
    'ticket_processing': 'info',
    'ticket_completed': 'good',
    'resource_returned': 'muted',
    'warranty_alert': 'warn',
    'sla_overdue': 'danger',
}


class Notification(TenantModel):
    recipient = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='notifications')
    kind = models.CharField(max_length=40)
    title = models.CharField(max_length=200)
    body = models.CharField(max_length=300, blank=True)
    link_url = models.CharField(max_length=300, blank=True)
    related_ticket = models.ForeignKey('tickets.Ticket', null=True, blank=True, on_delete=models.CASCADE)
    related_resource = models.ForeignKey(
        'resources.Resource', null=True, blank=True, on_delete=models.CASCADE)
    # Set for every notification (not just the ambient warranty/SLA ones): lifecycle
    # events use f'ticket_state:{ticket.id}:{ticket.request_status}' so a double-submit
    # can't create a duplicate row; ambient alerts use it to stay idempotent across
    # repeated dashboard visits. Left null (never '') so the partial unique constraint
    # below only applies to rows that actually opt into dedup.
    dedupe_key = models.CharField(max_length=200, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_on']
        constraints = [
            models.UniqueConstraint(
                fields=['recipient', 'dedupe_key'],
                condition=models.Q(dedupe_key__isnull=False),
                name='uniq_recipient_dedupe_key',
            )
        ]

    def __str__(self):
        return f'{self.kind} -> {self.recipient}'

    @property
    def icon(self):
        return KIND_ICONS.get(self.kind, 'bell')

    @property
    def color(self):
        return KIND_COLORS.get(self.kind, 'info')
