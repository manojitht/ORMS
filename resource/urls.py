from django.urls import path
from .import views


urlpatterns = [
    path('resources_list_table/', views.resources_list_table, name='resources_list_table'),
    path('add_resource_page/', views.add_resource_page, name='add_resource_page'),
    path('edit_resource/<int:resid>/', views.edit_resource, name='edit_resource'),
    path('update_resource/<int:resid>/', views.update_resource, name='update_resource'),
    path('delete_resource/<int:resid>/', views.delete_resource, name='delete_resource'),
    path('resource_deletion_history/', views.resource_deletion_history, name='resource_deletion_history'),
    path('restore_device/<int:resid>/', views.restore_device, name='restore_device'),
    path('permanent_delete_device/<int:resid>/', views.permanent_delete_device, name='permanent_delete_device'),
    path('resources_date_sort/', views.resources_date_sort, name='resources_date_sort'),
]