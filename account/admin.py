from django.contrib import admin
from .models import Account, AccountProfile


class AccountAdmin(admin.ModelAdmin):
    list_display = ('peoplesoft_id', 'first_name', 'last_name', 'email','department','team', 'role', 'date_joined', 'last_login', 'is_superadmin', 'is_active', 'ini_pas')
    list_display_links = ('peoplesoft_id', 'first_name', 'last_name')
    readonly_fields = ('email', 'date_joined', 'last_login', 'is_active')
    ordering = ('-date_joined',)

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

class AccountProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'home_address', 'contact_number', 'profile_image')

admin.site.register(Account, AccountAdmin)

admin.site.register(AccountProfile, AccountProfileAdmin)
