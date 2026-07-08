from django.db import models
from django.utils import timezone
from department.models import Department
from team.models import Team
from employees.models import Employee
from resources.models import Category, ResourceTaken

from companies.models import TenantModel

REQUEST_TYPE_CHOICES = [
    ('Request new', 'Request new'),
    ('Replacement', 'Replacement'),
    ('Support', 'Support'),
]

# Hardcoded SLA thresholds for v1 -- no per-category/per-company config UI
# exists yet, so these live as simple module constants rather than a
# configurable model. A ticket still sitting in Pending past this many
# hours, or still open past this many days total, is flagged overdue.
SLA_HOURS_TO_START_PROCESSING = 24
SLA_DAYS_TO_COMPLETE = 5

class Ticket(TenantModel):
    request_id = models.CharField(max_length=30)
    created_for = models.ForeignKey(Employee, on_delete=models.CASCADE)
    created_by = models.CharField(max_length=200)
    created_ps_id = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    # The Category being provisioned -- set for 'Request new'/'Replacement'
    # tickets, left null for 'Support' tickets (which reference an existing
    # assigned resource via regarding_resource_taken instead).
    requested_category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    # The specific already-assigned resource a 'Support' ticket concerns.
    regarding_resource_taken = models.ForeignKey(
        ResourceTaken, null=True, blank=True, on_delete=models.SET_NULL, related_name='support_tickets'
    )
    asset_id = models.CharField(max_length=20, blank=True)
    request_category = models.CharField(max_length=200, choices=REQUEST_TYPE_CHOICES)
    request_status = models.CharField(max_length=200)
    request_decription = models.TextField(max_length=300)
    request_response = models.TextField(max_length=300, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    # Set when a ticket first moves Pending -> Processing (see
    # approve_processing_request). Needed alongside created_on/completed_on
    # to compute response-time vs. resolution-time SLA metrics separately.
    processing_started_on = models.DateTimeField(null=True, blank=True)
    completed_on = models.DateTimeField(null=True, blank=True)
    assigned_to = models.CharField(max_length=16, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'ticket'
        verbose_name_plural = 'tickets'
        unique_together = ('company', 'request_id')

    def __str__(self):
        return self.request_id

    @property
    def is_overdue(self):
        """True if this ticket has blown past its SLA and is still open --
        drives an 'Overdue' badge on the IT admin request-list templates.
        Mirrors Resource.warranty_alert_level's shape: computed at request
        time from hardcoded thresholds, no background job needed.
        """
        if self.request_status in ('Completed', 'Cancelled'):
            return False
        now = timezone.now()
        if self.request_status == 'Pending':
            return now - self.created_on > timezone.timedelta(hours=SLA_HOURS_TO_START_PROCESSING)
        if self.request_status == 'Processing':
            return now - self.created_on > timezone.timedelta(days=SLA_DAYS_TO_COMPLETE)
        return False

    @property
    def resource_label(self):
        """What this ticket is 'about': the Category being provisioned for
        New/Replacement tickets, or the already-assigned resource's category
        for Support tickets. Used in templates and email subjects so neither
        has to duplicate the requested_category vs regarding_resource_taken
        branch itself.
        """
        if self.requested_category:
            return self.requested_category.resource_category
        if self.regarding_resource_taken:
            return self.regarding_resource_taken.asset_id.resource_category.resource_category
        return ''
