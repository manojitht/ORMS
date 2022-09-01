from sre_parse import Verbose
from tabnanny import verbose
from django.db import models
from datetime import datetime, date

# Create your models here.

class Department(models.Model):
    cost_code = models.CharField(max_length=150, unique=True)
    department_name = models.CharField(max_length=150, unique=True)
    department_head = models.CharField(max_length=150)
    created_by = models.CharField(max_length=150)
    created_on = models.DateField(auto_now_add=True)
    is_active = models.models.BooleanField(default=True)

    class Meta:
        verbose_name = 'department'
        verbose_name_plural = 'departments'

    def __str__(self):
        return self.department_name