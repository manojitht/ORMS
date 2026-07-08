from datetime import date, timedelta

from django.db import models
from department.models import Department
from team.models import Team
from employees.models import Employee

from companies.models import TenantModel

# How far ahead of a resource's warranty_expiry_date to start flagging it as
# "expiring soon" on the resources list/dashboards. Hardcoded for now -- no
# per-company config UI exists yet, and 30 days is a reasonable default lead
# time for reordering/renewing before a warranty actually lapses.
WARRANTY_ALERT_WINDOW_DAYS = 30


class Category(TenantModel):
    resource_category = models.CharField(max_length=200)
    description = models.CharField(max_length=255)
    category_image = models.ImageField(upload_to='photos/categories', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    # Whether resources in this category are physical, asset-id-tracked units
    # (laptops, monitors) vs. attribute-only records with nothing to hand out
    # or return (e.g. a software license) -- drives ticket-completion behavior.
    tracks_physical_asset = models.BooleanField(default=True)
    # Admin-defined custom fields for this category, e.g.
    # [{"key": "bitlocker_key", "label": "BitLocker Key"}, {"key": "imei", "label": "IMEI"}].
    # Lets different categories track different metadata without a fixed,
    # hardcoded field set -- values are stored per-Resource in attribute_values.
    attribute_schema = models.JSONField(default=list, blank=True)

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        unique_together = ('company', 'resource_category')

    def __str__(self):
        return self.resource_category

class Resource(TenantModel):
    asset_id = models.CharField(max_length=16)
    model_name = models.CharField(max_length=200)
    resource_category = models.ForeignKey(Category, on_delete=models.CASCADE)
    # Values for whichever custom attributes resource_category.attribute_schema
    # defines, e.g. {"bitlocker_key": "483-xxxx-xxxx"}.
    attribute_values = models.JSONField(default=dict, blank=True)
    resource_availability = models.CharField(max_length=200)
    resource_description = models.TextField(max_length=300, blank=True)
    added_by = models.CharField(max_length=200)
    resource_image = models.ImageField(upload_to='photos/resources', blank=True, null=True)
    added_on = models.DateField(auto_now_add=True)
    # When this resource's warranty/lease runs out. Optional and first-class
    # (not a schema-driven attribute_values entry) because alerts need to
    # filter/sort/aggregate on it in querysets -- a JSON dict value can't do
    # that efficiently.
    warranty_expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'resource'
        verbose_name_plural = 'resources'
        unique_together = ('company', 'asset_id')

    def __str__(self):
        return self.asset_id

    @property
    def warranty_alert_level(self):
        """'expired' / 'expiring_soon' / None, for a status-pill on resource
        list/detail pages and dashboard counts. Computed at request time
        rather than stored/synced, matching Ticket.resource_label's shape --
        there's no background job runner in this project to keep a stored
        flag in sync, so deriving it from today's date on read is the only
        option that can't drift stale.
        """
        if not self.warranty_expiry_date:
            return None
        today = date.today()
        if self.warranty_expiry_date < today:
            return 'expired'
        if self.warranty_expiry_date <= today + timedelta(days=WARRANTY_ALERT_WINDOW_DAYS):
            return 'expiring_soon'
        return None

class ResourceTaken(TenantModel):
    asset_id = models.ForeignKey(Resource, on_delete=models.CASCADE)
    peoplesoft_id = models.ForeignKey(Employee, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    added_by = models.CharField(max_length=200)
    assigned_by = models.CharField(null=True, blank=True, max_length=200)
    resource_status = models.CharField(max_length=200)
    taken_date = models.DateField(auto_now_add=True)
    returned_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    reason_notes = models.TextField(max_length=300, blank=True)
    manager_peoplesoft_id = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return str(self.asset_id)

class OtherAccessories(TenantModel):
    peoplesoft_id = models.OneToOneField(Employee, on_delete=models.CASCADE)
    other_notes = models.TextField(max_length=300, blank=True)

    def __str__(self):
        return str(self.peoplesoft_id)
