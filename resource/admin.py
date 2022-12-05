from django.contrib import admin
from .models import Resource, ResourceTaken, Category #calling the Resource cls model from the same resource app

# Registering Resource model here.
admin.site.register(Category)
admin.site.register(Resource)
admin.site.register(ResourceTaken)
# admin.site.register(OtherAccessories)
