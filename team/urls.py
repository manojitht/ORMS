from django.urls import path
from .import views


urlpatterns = [
    path('superadmin_list_team', views.superadmin_list_team, name='superadmin_list_team'),
    path('superadmin_add_team', views.superadmin_add_team, name='superadmin_add_team'),
]