from django.urls import path
from .import views


urlpatterns = [
    path('resources_list_table/', views.resources_list_table, name='resources_list_table'),
    path('returned_resources_list_table/', views.returned_resources_list_table, name='returned_resources_list_table'),
    path('taken_resources_list_table/', views.taken_resources_list_table, name='taken_resources_list_table'),
    path('resources_listings_page/', views.resources_listings_page, name='resources_listings_page'),
    path('add_resource_page/', views.add_resource_page, name='add_resource_page'),
    path('edit_resource/<int:resid>/', views.edit_resource, name='edit_resource'),
    path('update_resource/<int:resid>/', views.update_resource, name='update_resource'),
    path('delete_resource/<int:resid>/', views.delete_resource, name='delete_resource'),
    path('resource_deletion_history/', views.resource_deletion_history, name='resource_deletion_history'),
    path('restore_device/<int:resid>/', views.restore_device, name='restore_device'),
    path('permanent_delete_device/<int:resid>/', views.permanent_delete_device, name='permanent_delete_device'),
    path('resources_date_sort/', views.resources_date_sort, name='resources_date_sort'),
    path('returned_resources_date_sort/', views.returned_resources_date_sort, name='returned_resources_date_sort'),
    path('taken_resources_date_sort/', views.taken_resources_date_sort, name='taken_resources_date_sort'),
    path('it_admin_notes_page/', views.it_admin_notes_page, name='it_admin_notes_page'),
    path('view_resource/<int:resid>/', views.view_resource, name='view_resource'),
    path('view_resource_categories/', views.view_resource_categories, name='view_resource_categories'),
    path('add_category_page/', views.add_category_page, name='add_category_page'),
    path('edit_category_page/<int:catid>/', views.edit_category_page, name='edit_category_page'),
    path('delete_category_warning/<int:delcatid>/', views.delete_category_warning, name='delete_category_warning'),
]