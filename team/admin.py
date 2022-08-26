from django.contrib import admin
from .models import Team

# Register your models here.
class TeamAdmin(admin.ModelAdmin):
    list_display = ('team_name', 'department', 'created_date', 'is_active')
    ordering = ('-department',)

admin.site.register(Team, TeamAdmin)
