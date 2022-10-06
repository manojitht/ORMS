from distutils.command.upload import upload
from django.db import models
from department.models import Department
from team.models import Team


# Create your models here.

class Members(models.Model):
    peoplesoft_id = models.CharField(max_length=8, unique=True)
    fullname = models.CharField(max_length=150)
    position = models.CharField(max_length=150)
    email = models.EmailField(max_length=100,unique=True)
    contact = models.CharField(max_length=50)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    home_address = models.CharField(max_length=255)
    member_image = models.ImageField(upload_to='photos/members', blank=True, null=True)
    manager_name = models.CharField(max_length=150)
    manager_peoplesoft_id = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'member'
        verbose_name_plural = 'members'

    def __str__(self):
        return self.peoplesoft_id