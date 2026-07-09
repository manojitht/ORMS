from django.db import models

from account.models import Account
from companies.models import TenantModel

# Lucide icon + status-pill color variant per action, mirroring the same
# per-kind mapping notifications/models.py already uses for its rows -- see
# design-system.css's .status-pill for the shared color tokens.
ACTION_ICONS = {
    'ticket_created': 'plus-circle',
    'ticket_approved': 'check-circle',
    'ticket_denied': 'x-circle',
    'ticket_cancelled': 'x-circle',
    'ticket_processing_started': 'loader',
    'ticket_completed': 'check-circle',
    'resource_created': 'plus-circle',
    'resource_updated': 'pencil',
    'resource_restored': 'rotate-ccw',
    'resource_deleted': 'trash-2',
    'resource_taken': 'arrow-right-circle',
    'resource_returned': 'undo-2',
}
ACTION_COLORS = {
    'ticket_created': 'info',
    'ticket_approved': 'good',
    'ticket_denied': 'danger',
    'ticket_cancelled': 'danger',
    'ticket_processing_started': 'info',
    'ticket_completed': 'good',
    'resource_created': 'good',
    'resource_updated': 'info',
    'resource_restored': 'good',
    'resource_deleted': 'danger',
    'resource_taken': 'info',
    'resource_returned': 'muted',
}


class ActivityEntry(TenantModel):
    actor = models.ForeignKey(Account, null=True, on_delete=models.SET_NULL, related_name='activity_entries')
    action = models.CharField(max_length=40)
    # Self-contained sentence with the asset_id/request_id baked in at
    # creation time -- related_resource/related_ticket below go null on a
    # hard delete of their target, so this is what keeps the entry
    # meaningful after the thing it's about is gone.
    summary = models.CharField(max_length=500)
    related_resource = models.ForeignKey(
        'resources.Resource', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='activity_entries')
    related_ticket = models.ForeignKey(
        'tickets.Ticket', null=True, blank=True, on_delete=models.SET_NULL, related_name='activity_entries')
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        # -id as a tiebreaker: two entries logged in the same request (e.g.
        # a ticket-completion that also logs a resource_taken row) can land
        # on the same auto_now_add timestamp depending on datetime
        # resolution, and insertion order is still the correct newest-first
        # order in that case.
        ordering = ['-created_on', '-id']

    def __str__(self):
        return self.summary

    @property
    def icon(self):
        return ACTION_ICONS.get(self.action, 'activity')

    @property
    def color(self):
        return ACTION_COLORS.get(self.action, 'info')
