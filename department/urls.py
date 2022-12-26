from django.urls import path
from .import views


urlpatterns = [
    path('display_departments/<int:depid>/', views.display_departments, name='display_departments'),
    path('add_new_department', views.add_new_department, name='add_new_department'),
    path('delete_department/<int:depid>/', views.delete_department, name='delete_department'),
    path('edit_department/<int:depid>/', views.edit_department, name='edit_department'),
    path('update_department/<int:depid>/', views.update_department, name='update_department'),
    # path('restore_department/<int:depid>/', views.restore_department, name='restore_department'),
    # path('permanent_delete_department/<int:depid>/', views.permanent_delete_department, name='permanent_delete_department'),
    # path('search_department/', views.search_department, name='search_department'),
    path('superadmin_department_table/', views.superadmin_department_table, name='superadmin_department_table'),
    path('superadmin_department_date_sort/', views.superadmin_department_date_sort, name='superadmin_department_date_sort'),
    path('department_view_teams/<int:depid>/', views.department_view_teams, name='department_view_teams'),
    path('notes_page', views.notes_page, name='notes_page'),
    path('department_deletion_history/', views.department_deletion_history, name='department_deletion_history'),
]