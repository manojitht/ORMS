from django.db import models
from department.models import Department
from team.models import Team
from members.models import Members


# Create your models here.

class Resource(models.Model):
    asset_id = models.CharField(max_length=16, unique=True)
    device_type = models.CharField(max_length=200)
    bitlocker_key = models.CharField(max_length=200, blank=True)
    device_availability = models.CharField(max_length=200)
    device_description = models.TextField(max_length=300, blank=True)
    added_by = models.CharField(max_length=200)
    device_image = models.ImageField(upload_to='photos/resources', blank=True, null=True)
    added_on = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'resource'
        verbose_name_plural = 'resources'

    def __str__(self):
        return self.asset_id

class ResourceTaken(models.Model):
    asset_id = models.ForeignKey(Resource, on_delete=models.CASCADE)
    peoplesoft_id = models.ForeignKey(Members, on_delete=models.CASCADE)
    device_type = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    added_by = models.CharField(max_length=200)
    device_status = models.CharField(max_length=200)
    taken_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.asset_id

class OtherAccessories(models.Model):
    peoplesoft_id = models.OneToOneField(Members, on_delete=models.CASCADE)
    keyboard = models.CharField(blank=True, max_length=100)
    mouse = models.CharField(blank=True, max_length=100)
    network_adapter = models.CharField(blank=True, max_length=100)
    headset = models.CharField(blank=True, max_length=100)
    other_notes = models.TextField(max_length=300, blank=True)

    def __str__(self):
        return self.peoplesoft_id

