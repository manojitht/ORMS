from django.db import models
from department.models import Department
from team.models import Team

from companies.models import TenantModel


class Employee(TenantModel):
    peoplesoft_id = models.CharField(max_length=8)
    fullname = models.CharField(max_length=150)
    position = models.CharField(max_length=150)
    email = models.EmailField(max_length=100)
    contact = models.CharField(max_length=50)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    home_address = models.CharField(max_length=255)
    member_image = models.ImageField(upload_to='photos/members', blank=True, null=True)
    manager_name = models.CharField(max_length=150)
    manager_peoplesoft_id = models.CharField(max_length=150)
    date_joined = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'employee'
        verbose_name_plural = 'employees'
        unique_together = (('company', 'peoplesoft_id'), ('company', 'email'))

    def __str__(self):
        return self.peoplesoft_id
