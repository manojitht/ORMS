from django.db import models
from department.models import Department

from companies.models import TenantModel


class Team(TenantModel):
    team_name = models.CharField(max_length=200)
    team_head = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    team_description = models.TextField(max_length=255, blank=True)
    created_by = models.CharField(max_length=200)
    created_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'team'
        verbose_name_plural = 'teams'
        unique_together = ('company', 'team_name')

    def __str__(self):
        return self.team_name
