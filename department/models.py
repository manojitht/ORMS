from sre_parse import Verbose
from tabnanny import verbose
from django.db import models

# Create your models here.

class Department(models.Model):
    department_name = models.CharField(max_length=150, unique=True)

    class Meta:
        verbose_name = 'department'
        verbose_name_plural = 'departments'

    def __str__(self):
        return self.department_name