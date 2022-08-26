from tkinter import CASCADE
from unicodedata import category
from django.db import models
from department.models import Department

# Create your models here.
class Team(models.Model):
    team_name = models.CharField(max_length=200, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.team_name