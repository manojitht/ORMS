from django.urls import path
from .import views


app_name = 'team'

urlpatterns = [
    path('display_team/<int:temid>/', views.display_team, name='display_team'),
    path('superadmin_add_team/', views.superadmin_add_team, name='superadmin_add_team'),
    path('edit_team/<int:temid>/', views.edit_team, name='edit_team'),
    path('update_team/<int:temid>/', views.update_team, name='update_team'),
    path('delete_team/<int:temid>/', views.delete_team, name='delete_team'),
    path('superadmin_team_table/', views.superadmin_team_table, name='superadmin_team_table'),
    path('superadmin_team_date_sort/', views.superadmin_team_date_sort, name='superadmin_team_date_sort'),
    path('team_deletion_history/', views.team_deletion_history, name='team_deletion_history'),
]