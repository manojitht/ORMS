from django.db import models

from companies.models import TenantModel


class Department(TenantModel):
    department_name = models.CharField(max_length=150)
    department_head = models.CharField(max_length=150)
    department_description = models.TextField(max_length=255, blank=True)
    created_by = models.CharField(max_length=150)
    created_on = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'department'
        verbose_name_plural = 'departments'
        unique_together = ('company', 'department_name')

    def __str__(self):
        return self.department_name
