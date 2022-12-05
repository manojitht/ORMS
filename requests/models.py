from django.db import models
from department.models import Department
from team.models import Team
from members.models import Members

# Create your models here.

class Requests(models.Model):
    request_id = models.CharField(max_length=30, unique=True)
    created_for = models.ForeignKey(Members, on_delete=models.CASCADE)
    created_by = models.CharField(max_length=200)
    created_ps_id = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    request_resource = models.CharField(max_length=200)
    asset_id = models.CharField(max_length=20, blank=True)
    request_category = models.CharField(max_length=200)
    request_status = models.CharField(max_length=200)
    request_decription = models.TextField(max_length=300)
    request_response = models.TextField(max_length=300, blank=True)
    created_on = models.DateField(auto_now_add=True)
    completed_on = models.DateField(null=True, blank=True)
    assigned_to = models.CharField(max_length=16, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'request'
        verbose_name_plural = 'requests'

    def __str__(self):
        return self.request_id