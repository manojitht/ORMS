from django.contrib import admin
from .models import Resource #calling the Resource cls model from the same resource app

# Registering Resource model here.
admin.site.register(Resource)
