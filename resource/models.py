from django.db import models

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

