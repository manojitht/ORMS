from django.urls import path
from .import views


urlpatterns = [
    path('superadmin_add_department', views.superadmin_add_department, name='superadmin_add_department'),
    path('delete_department/<int:depid>/', views.delete_department, name='delete_department'),
    path('edit_department/<int:depid>/', views.edit_department, name='edit_department'),
]