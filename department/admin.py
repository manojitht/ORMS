from django.contrib import admin
from .models import Department #calling the Department cls model from the same department app

# Registering Department model here.
admin.site.register(Department)
