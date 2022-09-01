from django.urls import path
from .import views


urlpatterns = [
    path('superadmin_add_department', views.superadmin_add_department, name='superadmin_add_department'),
]