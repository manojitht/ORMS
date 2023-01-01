from django.db import models
from department.models import Department
from team.models import Team
from members.models import Members


# Create your models here.

class Category(models.Model):
    resource_category = models.CharField(max_length=200)
    description = models.CharField(max_length=255)
    category_image = models.ImageField(upload_to='photos/categories', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.resource_category

class Resource(models.Model):
    asset_id = models.CharField(max_length=16, unique=True)
    model_name = models.CharField(max_length=200)
    resource_category = models.ForeignKey(Category, on_delete=models.CASCADE)
    bitlocker_key = models.CharField(max_length=200, blank=True)
    resource_availability = models.CharField(max_length=200)
    resource_description = models.TextField(max_length=300, blank=True)
    added_by = models.CharField(max_length=200)
    resource_image = models.ImageField(upload_to='photos/resources', blank=True, null=True)
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
    resource_category = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    added_by = models.CharField(max_length=200)
    assigned_by = models.CharField(null=True, blank=True, max_length=200)
    resource_status = models.CharField(max_length=200)
    taken_date = models.DateField(auto_now_add=True)
    returned_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    reason_notes = models.TextField(max_length=300, blank=True)

    def __str__(self):
        return self.asset_id

class OtherAccessories(models.Model):
    peoplesoft_id = models.OneToOneField(Members, on_delete=models.CASCADE)
    other_notes = models.TextField(max_length=300, blank=True)

    def __str__(self):
        return self.peoplesoft_id

