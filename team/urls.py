from django.urls import path
from .import views


urlpatterns = [
    path('superadmin_list_team', views.superadmin_list_team, name='superadmin_list_team'),
    path('superadmin_add_team/', views.superadmin_add_team, name='superadmin_add_team'),
    path('edit_team/<int:temid>/', views.edit_team, name='edit_team'),
    path('update_team/<int:temid>/', views.update_team, name='update_team'),
    path('delete_team/<int:temid>/', views.delete_team, name='delete_team'),
    path('restore_team/<int:temid>/', views.restore_team, name='restore_team'),
    path('permanent_delete_team/<int:temid>/', views.permanent_delete_team, name='permanent_delete_team'),
    path('superadmin_team_table/', views.superadmin_team_table, name='superadmin_team_table'),
    path('superadmin_team_date_sort/', views.superadmin_team_date_sort, name='superadmin_team_date_sort'),
    path('team_deletion_history/', views.team_deletion_history, name='team_deletion_history'),
    #path('back_to_team_view/<int:temid>/', views.back_to_team_view, name='back_to_team_view'),
    #path('superadmin_list_by_team', views.superadmin_list_by_team, name='superadmin_list_by_team'),
    #path('edit_department/<int:depid>/', views.edit_department, name='edit_department'),
]