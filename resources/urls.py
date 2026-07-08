from django.urls import path
from .import views


app_name = 'resources'

urlpatterns = [
    path('resources_list_table/', views.resources_list_table, name='resources_list_table'),
    path('export_resources_csv/', views.export_resources_csv, name='export_resources_csv'),
    path('import_resources_csv/', views.import_resources_csv, name='import_resources_csv'),
    path('download_resource_import_template_csv/', views.download_resource_import_template_csv, name='download_resource_import_template_csv'),
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
    path('view_resource/<int:resid>/', views.view_resource, name='view_resource'),
    path('expiring_resources/', views.expiring_resources_page, name='expiring_resources_page'),
    path('resource_qr_image/<int:resid>/', views.resource_qr_image, name='resource_qr_image'),
    path('print_resource_label/<int:resid>/', views.print_resource_label, name='print_resource_label'),
    path('scan/<str:asset_id>/', views.scan_resource, name='scan_resource'),
    path('scan_camera/', views.scan_camera_page, name='scan_camera_page'),
    path('view_resource_categories/', views.view_resource_categories, name='view_resource_categories'),
    path('add_category_page/', views.add_category_page, name='add_category_page'),
    path('edit_category_page/<int:catid>/', views.edit_category_page, name='edit_category_page'),
    path('update_category/<int:catid>/', views.update_category, name='update_category'),
    path('delete_category_warning/<int:delcatid>/', views.delete_category_warning, name='delete_category_warning'),
    path('search_resource/', views.search_resource, name='search_resource'),


    path('manager_returned_resources_list_table/<int:userid>/', views.manager_returned_resources_list_table, name='manager_returned_resources_list_table'),
    path('manager_taken_resources_list_table/<int:userid>/', views.manager_taken_resources_list_table, name='manager_taken_resources_list_table'),
    path('employee_taken_resources_list_table/<int:userid>/', views.employee_taken_resources_list_table, name='employee_taken_resources_list_table'),
    path('manager_returned_resources_date_sort/<int:userid>/', views.manager_returned_resources_date_sort, name='manager_returned_resources_date_sort'),
    path('manager_taken_resources_date_sort/<int:userid>/', views.manager_taken_resources_date_sort, name='manager_taken_resources_date_sort'),

    
]