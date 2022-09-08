from django.urls import path
from .import views


urlpatterns = [
    path('superadmin_list_department', views.superadmin_list_department, name='superadmin_list_department'),
    path('add_new_department', views.add_new_department, name='add_new_department'),
    path('delete_department/<int:depid>/', views.delete_department, name='delete_department'),
    path('edit_department/<int:depid>/', views.edit_department, name='edit_department'),
]