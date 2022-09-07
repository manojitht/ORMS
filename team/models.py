from tkinter import CASCADE
from unicodedata import category
from django.db import models
from department.models import Department

# Create your models here.
class Team(models.Model):
    team_name = models.CharField(max_length=200, unique=True)
    team_head = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    #department = models.CharField(max_length=200)
    created_by = models.CharField(max_length=200)
    created_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'team'
        verbose_name_plural = 'teams'

    def __str__(self):
        return self.team_name