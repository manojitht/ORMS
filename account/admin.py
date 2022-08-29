from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account

# Register your models here.

class AccountAdmin(admin.ModelAdmin):
    list_display = ('peoplesoft_id', 'first_name', 'last_name', 'email','department','team', 'role', 'date_joined', 'last_login', 'is_superadmin', 'is_active')
    list_display_links = ('peoplesoft_id', 'first_name', 'last_name')
    readonly_fields = ('email', 'date_joined', 'last_login', 'is_active')
    ordering = ('-date_joined',) # "-" refers to decending format of dateofjoin

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

admin.site.register(Account, AccountAdmin)
